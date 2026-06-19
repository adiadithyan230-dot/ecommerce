import os
import json
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, DeleteView
from django.urls import reverse_lazy

from .models import Dataset
from .forms import DatasetForm
from analytics.cleaning_engine import clean_data, detect_issues, validate_columns, calculate_quality_score
from users.audit import log_action


def can_manage_datasets(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'analyst'])


class DatasetManagerRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not can_manage_datasets(request.user):
            raise PermissionDenied("Your role can view dashboards but cannot manage datasets.")
        return super().dispatch(request, *args, **kwargs)

@method_decorator(login_required, name='dispatch')
class DatasetListView(ListView):
    model = Dataset
    template_name = 'datasets/list.html'
    context_object_name = 'datasets'

    def get_queryset(self):
        queryset = Dataset.objects.filter(uploaded_by=self.request.user)
        search = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        sort = self.request.GET.get('sort', '-uploaded_at')

        if search:
            queryset = queryset.filter(name__icontains=search)
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)

        allowed_sorts = {'name', '-name', 'uploaded_at', '-uploaded_at', 'quality_score', '-quality_score'}
        if sort not in allowed_sorts:
            sort = '-uploaded_at'
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['sort_filter'] = self.request.GET.get('sort', '-uploaded_at')
        return context

@method_decorator(login_required, name='dispatch')
class DatasetUploadView(DatasetManagerRequiredMixin, CreateView):
    model = Dataset
    form_class = DatasetForm
    template_name = 'datasets/upload.html'
    success_url = reverse_lazy('datasets:list')

    def form_valid(self, form):
        dataset = form.save(commit=False)
        dataset.uploaded_by = self.request.user
        
        # Temporary save file to process it
        dataset.file = self.request.FILES['file']
        super().form_valid(form) # Saves the file to disk
        
        # Read the file with Pandas
        filepath = self.object.file.path
        try:
            df = pd.read_csv(filepath)
            
            # Detect Issues
            issues = detect_issues(df)
            
            # Clean data
            df_cleaned = clean_data(df)
            
            # Validate columns
            is_valid, missing = validate_columns(df_cleaned)
            quality_score, quality_grade = calculate_quality_score(issues, missing)
            if not is_valid:
                # Delete the uploaded file and record
                self.object.delete()
                form.add_error('file', f"Missing required columns in dataset: {', '.join(missing)}")
                return self.form_invalid(form)
            
            # Save the cleaned dataframe back to the filepath
            df_cleaned.to_csv(filepath, index=False)
            
            # Update dataset metadata
            self.object.row_count = len(df_cleaned)
            self.object.column_count = len(df_cleaned.columns)
            self.object.quality_score = quality_score
            self.object.quality_grade = quality_grade
            self.object.summary = json.dumps(issues)
            self.object.is_active = True # Automatically make the newly uploaded dataset active
            self.object.save()
            log_action(self.request.user, 'dataset_upload', self.object.name, f"Quality score: {quality_score} ({quality_grade})")
            
            messages.success(self.request, f"Dataset '{self.object.name}' uploaded, cleaned, and activated successfully. Quality score: {quality_score}/100 ({quality_grade}).")
        except Exception as e:
            if self.object.pk:
                self.object.delete()
            form.add_error('file', f"Error reading/cleaning CSV file: {str(e)}")
            return self.form_invalid(form)
            
        return redirect(self.success_url)

@login_required
def activate_dataset(request, pk):
    if not can_manage_datasets(request.user):
        raise PermissionDenied("Your role can view dashboards but cannot activate datasets.")
    dataset = get_object_or_404(Dataset, pk=pk, uploaded_by=request.user)
    dataset.is_active = True
    dataset.save()
    log_action(request.user, 'dataset_activate', dataset.name)
    messages.success(request, f"Dataset '{dataset.name}' activated successfully!")
    return redirect('datasets:list')

@login_required
def preview_dataset(request, pk):
    dataset = get_object_or_404(Dataset, pk=pk, uploaded_by=request.user)
    try:
        df = pd.read_csv(dataset.file.path)
        preview_data = df.head(15).to_dict(orient='records')
        columns = df.columns.tolist()
        summary = json.loads(dataset.summary) if dataset.summary else {}
    except Exception as e:
        messages.error(request, f"Error previewing dataset: {str(e)}")
        preview_data, columns, summary = [], [], {}
        
    return render(request, 'datasets/preview.html', {
        'dataset': dataset,
        'preview_data': preview_data,
        'columns': columns,
        'summary': summary
    })

@method_decorator(login_required, name='dispatch')
class DatasetDeleteView(DatasetManagerRequiredMixin, DeleteView):
    model = Dataset
    template_name = 'datasets/confirm_delete.html'
    success_url = reverse_lazy('datasets:list')

    def get_queryset(self):
        return Dataset.objects.filter(uploaded_by=self.request.user)

    def delete(self, request, *args, **kwargs):
        dataset = self.get_object()
        # Delete file from storage
        if dataset.file and os.path.exists(dataset.file.path):
            try:
                os.remove(dataset.file.path)
            except OSError as e:
                messages.warning(request, f"Note: The file '{dataset.file.name}' could not be deleted from disk because it is in use by another process, but the database record has been removed.")
        log_action(request.user, 'dataset_delete', dataset.name)
        messages.success(request, f"Dataset '{dataset.name}' deleted successfully!")
        return super().delete(request, *args, **kwargs)
