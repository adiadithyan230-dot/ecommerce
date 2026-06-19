import os
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import CreateView, UpdateView, TemplateView
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views import View

from .forms import CustomUserCreationForm, UserProfileForm
from .models import AuditLog, CustomUser
from .audit import log_action
from datasets.models import Dataset

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    template_name = 'registration/signup.html'

class UserLoginView(LoginView):
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

class UserLogoutView(LogoutView):
    next_page = reverse_lazy('users:login')

@method_decorator(login_required, name='dispatch')
class ProfileView(UpdateView):
    model = CustomUser
    form_class = UserProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')

    def get_object(self, queryset=None):
        return self.request.user

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Enforces that the user is authenticated and is an admin/superuser.
    """
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.role == 'admin' or self.request.user.is_superuser)

@method_decorator(login_required, name='dispatch')
class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'users/admin_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['users'] = CustomUser.objects.all().order_by('-date_joined')
        context['datasets'] = Dataset.objects.all().order_by('-uploaded_at')
        
        # System KPIs
        context['total_users'] = CustomUser.objects.count()
        context['active_users'] = CustomUser.objects.filter(is_active=True).count()
        context['total_datasets'] = Dataset.objects.count()
        context['active_datasets'] = Dataset.objects.filter(is_active=True).count()
        context['role_choices'] = CustomUser.ROLE_CHOICES
        context['audit_logs'] = AuditLog.objects.select_related('actor')[:25]
        
        return context

@method_decorator(login_required, name='dispatch')
class UpdateUserRoleView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        new_role = request.POST.get('role')
        if new_role in dict(CustomUser.ROLE_CHOICES):
            old_role = user.get_role_display()
            user.role = new_role
            user.save()
            log_action(request.user, 'role_change', user.username, f"{old_role} -> {user.get_role_display()}")
            messages.success(request, f"Updated role of {user.username} to {user.get_role_display()}.")
        else:
            messages.error(request, "Invalid role selected.")
        return redirect('users:admin_dashboard')

@method_decorator(login_required, name='dispatch')
class ToggleUserStatusView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot deactivate your own account.")
        else:
            user.is_active = not user.is_active
            user.save()
            status_str = "activated" if user.is_active else "deactivated"
            log_action(request.user, 'user_status', user.username, status_str)
            messages.success(request, f"Successfully {status_str} user {user.username}.")
        return redirect('users:admin_dashboard')

@method_decorator(login_required, name='dispatch')
class DeleteUserView(AdminRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(CustomUser, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot delete your own account.")
        else:
            username = user.username
            log_action(request.user, 'user_delete', username)
            user.delete()
            messages.success(request, f"User {username} deleted successfully.")
        return redirect('users:admin_dashboard')

@method_decorator(login_required, name='dispatch')
class DeleteDatasetView(AdminRequiredMixin, View):
    def post(self, request, pk):
        dataset = get_object_or_404(Dataset, pk=pk)
        name = dataset.name
        if dataset.file and os.path.exists(dataset.file.path):
            try:
                os.remove(dataset.file.path)
            except OSError as e:
                messages.warning(request, f"Note: The file '{dataset.file.name}' could not be deleted from disk because it is in use by another process, but the database record has been removed.")
        log_action(request.user, 'dataset_delete', name)
        dataset.delete()
        messages.success(request, f"Dataset '{name}' deleted successfully.")
        return redirect('users:admin_dashboard')
