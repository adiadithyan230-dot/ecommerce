import json
import pandas as pd
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST
from urllib.parse import urlencode

from analytics.data_loader import load_data
from analytics.analytics_engine import filter_dataframe, calculate_kpis, generate_forecast
from analytics.insight_engine import generate_insights
from analytics import chart_engine
from analytics import export_engine
from .models import SavedFilterView
from users.audit import log_action
from ai_insights.models import AIInsight


def can_export_reports(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'analyst'])

def can_generate_ai_insights(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'analyst'])

def get_filters_from_request(request):
    """
    Extracts dashboard filter values from the HTTP request.
    """
    return {
        'date_start': request.GET.get('date_start'),
        'date_end': request.GET.get('date_end'),
        'category': request.GET.getlist('category') if request.GET.getlist('category') else None,
        'region': request.GET.getlist('region') if request.GET.getlist('region') else None,
        'payment_method': request.GET.getlist('payment_method') if request.GET.getlist('payment_method') else None,
        'order_status': request.GET.getlist('order_status') if request.GET.getlist('order_status') else None,
        'revenue_min': request.GET.get('revenue_min'),
        'revenue_max': request.GET.get('revenue_max'),
        'product_search': request.GET.get('product_search'),
    }

def build_date_preset_links(request, df):
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    if not date_cols:
        return []

    dates = pd.to_datetime(df[date_cols[0]], errors='coerce').dropna()
    if dates.empty:
        return []

    anchor = dates.max().normalize()
    presets = [
        ('Last 7 days', anchor - pd.Timedelta(days=6), anchor),
        ('This month', anchor.replace(day=1), anchor),
        ('Last quarter', (anchor - pd.DateOffset(months=3)).to_period('Q').start_time, (anchor - pd.DateOffset(months=3)).to_period('Q').end_time.normalize()),
        ('This year', anchor.replace(month=1, day=1), anchor),
    ]

    links = []
    for label, start, end in presets:
        params = request.GET.copy()
        params['date_start'] = start.strftime('%Y-%m-%d')
        params['date_end'] = end.strftime('%Y-%m-%d')
        params.pop('page', None)
        links.append({'label': label, 'query': params.urlencode()})
    return links

def build_forecast_context(df, forecast):
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    monthly_history = []

    if date_cols and 'revenue' in df.columns:
        date_col = date_cols[0]
        history_df = df.copy()
        history_df[date_col] = pd.to_datetime(history_df[date_col], errors='coerce')
        history_df = history_df.dropna(subset=[date_col])
        if not history_df.empty:
            monthly = history_df.groupby(history_df[date_col].dt.to_period('M'))['revenue'].sum().sort_index()
            monthly_history = [
                {'period': str(period), 'revenue': round(float(revenue), 2)}
                for period, revenue in monthly.tail(6).items()
            ]

    month_count = len(monthly_history)
    if month_count >= 6:
        confidence = 'Moderate'
        note = 'Forecast is based on multiple historical months, but it still uses a simple linear trend.'
    elif month_count >= 3:
        confidence = 'Low'
        note = 'Forecast has the minimum history needed for trend regression. Treat it as directional.'
    else:
        confidence = 'Unavailable'
        note = 'At least 3 months of valid revenue history are required to generate a forecast.'

    return {
        'monthly_history': monthly_history,
        'month_count': month_count,
        'confidence': confidence,
        'note': note,
        'has_enough_history': month_count >= 3 and bool(forecast),
    }

@login_required
def index(request):
    df = load_data()
    
    if df is None or df.empty:
        return render(request, 'dashboard/index.html', {'no_data': True})
        
    filters = get_filters_from_request(request)
    filtered_df = filter_dataframe(df, filters)
    
    # Calculate KPIs
    kpis = calculate_kpis(filtered_df)
    
    # Generate Plotly charts in JSON format
    monthly_trend = chart_engine.generate_monthly_sales_trend(filtered_df)
    category_rev = chart_engine.generate_revenue_by_category(filtered_df)
    region_rev = chart_engine.generate_revenue_by_region(filtered_df)
    payment_methods = chart_engine.generate_payment_methods(filtered_df)
    order_status = chart_engine.generate_order_status(filtered_df)
    top_products = chart_engine.generate_top_products(filtered_df)
    daily_trend = chart_engine.generate_daily_revenue(filtered_df)
    heatmap = chart_engine.generate_revenue_heatmap(filtered_df)
    
    # Paginate Order Table
    orders_list = filtered_df.to_dict(orient='records')
    paginator = Paginator(orders_list, 10) # 10 orders per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Filter options for sidebar
    filter_options = {
        'categories': sorted(df['category'].dropna().unique().tolist()) if 'category' in df.columns else [],
        'regions': sorted(df['region'].dropna().unique().tolist()) if 'region' in df.columns else [],
        'payment_methods': sorted(df['payment_method'].dropna().unique().tolist()) if 'payment_method' in df.columns else [],
        'order_statuses': sorted(df['order_status'].dropna().unique().tolist()) if 'order_status' in df.columns else []
    }
    date_presets = build_date_preset_links(request, df)
    saved_filter_views = SavedFilterView.objects.filter(user=request.user)
    
    # Generate Business Insights
    insights = generate_insights(filtered_df, kpis)
    forecast = generate_forecast(filtered_df)
    forecast_meta = build_forecast_context(filtered_df, forecast)
    selected_ai_insight = None
    ai_insight_id = request.GET.get('ai_insight')
    if ai_insight_id:
        selected_ai_insight = AIInsight.objects.filter(id=ai_insight_id).select_related('created_by').first()
    
    context = {
        'kpis': kpis,
        'monthly_trend': monthly_trend,
        'category_rev': category_rev,
        'region_rev': region_rev,
        'payment_methods': payment_methods,
        'order_status': order_status,
        'top_products': top_products,
        'daily_trend': daily_trend,
        'heatmap': heatmap,
        'page_obj': page_obj,
        'filter_options': filter_options,
        'date_presets': date_presets,
        'saved_filter_views': saved_filter_views,
        'active_filters': filters,
        'insights': insights,
        'forecast': forecast,
        'forecast_meta': forecast_meta,
        'selected_ai_insight': selected_ai_insight,
        'can_generate_ai_insights': can_generate_ai_insights(request.user),
    }

    
    # Check if request is HTMX or AJAX to only render partial fragments
    if request.headers.get('HX-Request') == 'true' or request.GET.get('ajax') == 'true':
        return render(request, 'dashboard/partials/dashboard_content.html', context)
        
    return render(request, 'dashboard/index.html', context)

@login_required
def export_report(request, format_type):
    if not can_export_reports(request.user):
        raise PermissionDenied("Your role can view dashboards but cannot export reports.")

    df = load_data()
    if df is None or df.empty:
        return HttpResponse("No data to export", status=400)
        
    filters = get_filters_from_request(request)
    filtered_df = filter_dataframe(df, filters)
    kpis = calculate_kpis(filtered_df)
    
    filename = f"sales_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format_type == 'csv':
        csv_bytes = export_engine.export_csv(filtered_df)
        response = HttpResponse(csv_bytes, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}.csv"'
        log_action(request.user, 'export_report', f'{filename}.csv')
        return response
        
    elif format_type == 'excel':
        excel_bytes = export_engine.export_excel(filtered_df, kpis)
        response = HttpResponse(excel_bytes, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}.xlsx"'
        log_action(request.user, 'export_report', f'{filename}.xlsx')
        return response
        
    elif format_type == 'pdf':
        pdf_bytes = export_engine.export_pdf(filtered_df, kpis)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}.pdf"'
        log_action(request.user, 'export_report', f'{filename}.pdf')
        return response
        
    return HttpResponse("Invalid format", status=400)

@login_required
@require_POST
def save_filter_view(request):
    name = request.POST.get('name', '').strip()
    query_string = request.POST.get('query_string', '').strip()

    if not name:
        messages.error(request, "Enter a name before saving this filter view.")
        return redirect('dashboard:index')

    SavedFilterView.objects.update_or_create(
        user=request.user,
        name=name,
        defaults={'query_string': query_string},
    )
    messages.success(request, f"Saved filter view '{name}'.")
    target = reverse('dashboard:index')
    if query_string:
        target = f"{target}?{query_string}"
    return redirect(target)

@login_required
def forecast_view(request):
    df = load_data()

    if df is None or df.empty:
        return render(request, 'dashboard/forecast.html', {'no_data': True})

    forecast = generate_forecast(df)
    forecast_chart = chart_engine.generate_forecast_chart(forecast)
    forecast_meta = build_forecast_context(df, forecast)

    return render(request, 'dashboard/forecast.html', {
        'forecast': forecast,
        'forecast_chart': forecast_chart,
        'forecast_meta': forecast_meta,
    })

def about_view(request):
    return render(request, 'dashboard/docs/about.html')

def methodology_view(request):
    return render(request, 'dashboard/docs/methodology.html')

def dataset_info_view(request):
    return render(request, 'dashboard/docs/dataset_info.html')

def flow_view(request):
    return render(request, 'dashboard/docs/flow.html')

def viva_view(request):
    return render(request, 'dashboard/docs/viva.html')
