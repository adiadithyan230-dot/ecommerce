import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import reverse

from analytics.analytics_engine import calculate_kpis, filter_dataframe
from analytics.data_loader import load_data
from dashboard.views import get_filters_from_request

from .models import AIInsight
from .ollama_client import OllamaInsightError, generate_sales_insights


def can_generate_ai_insights(user):
    return user.is_authenticated and (user.is_superuser or user.role in ['admin', 'analyst'])


@login_required
def generate_insight(request):
    if request.method != 'POST':
        return redirect('dashboard:index')

    if not can_generate_ai_insights(request.user):
        raise PermissionDenied('Your role can view saved insights but cannot generate new AI insights.')

    df = load_data()
    if df is None or df.empty:
        messages.error(request, 'Upload or activate a dataset before generating AI insights.')
        return redirect('dashboard:index')

    filters = get_filters_from_request(request)
    filtered_df = filter_dataframe(df, filters)
    kpis = calculate_kpis(filtered_df)
    kpi_text = build_kpi_text(filtered_df, kpis)

    try:
        generated_text = generate_sales_insights(kpi_text)
    except OllamaInsightError as exc:
        messages.error(request, str(exc))
        return _dashboard_redirect(request)

    insight = AIInsight.objects.create(
        generated_text=generated_text,
        model_name=settings.OLLAMA_MODEL,
        created_by=request.user,
    )
    messages.success(request, 'AI sales insight generated and saved.')
    return _dashboard_redirect(request, insight_id=insight.id)


@login_required
def history(request):
    insights = AIInsight.objects.select_related('created_by').all()
    return render(request, 'ai_insights/history.html', {'insights': insights})


def build_kpi_text(df, kpis):
    lines = [
        f"Revenue: Rs {kpis.get('total_revenue', 0):,.2f}",
        f"Orders: {kpis.get('total_orders', 0)}",
        f"Average Order Value: Rs {kpis.get('aov', 0):,.2f}",
        f"Cancellation Rate: {kpis.get('cancellation_rate', 0):.2f}%",
        f"Return Rate: {kpis.get('return_rate', 0):.2f}%",
        f"Returning Customer Rate: {kpis.get('returning_customer_rate', 0):.2f}%",
        f"Top Region: {kpis.get('top_region', 'N/A')}",
        f"Top Category: {kpis.get('top_category', 'N/A')}",
        '',
        'Top Products:',
        *_top_items(df, 'product', value_col='revenue'),
        '',
        'Top Categories:',
        *_top_items(df, 'category', value_col='revenue'),
        '',
        'Region Sales:',
        *_top_items(df, 'region', value_col='revenue'),
        '',
        'Payment Methods:',
        *_top_items(df, 'payment_method'),
        '',
        'Order Status Summary:',
        *_top_items(df, 'order_status'),
    ]
    return '\n'.join(lines)


def _top_items(df, group_col, value_col=None, limit=5):
    if df is None or df.empty or group_col not in df.columns:
        return ['- N/A']

    if value_col and value_col in df.columns:
        series = df.groupby(group_col)[value_col].sum().sort_values(ascending=False).head(limit)
        return [f"- {name}: Rs {value:,.2f}" for name, value in series.items()]

    series = df[group_col].fillna('Unknown').value_counts().head(limit)
    return [f"- {name}: {count}" for name, count in series.items()]


def _dashboard_redirect(request, insight_id=None):
    params = request.GET.copy()
    if insight_id:
        params['ai_insight'] = insight_id
    url = reverse('dashboard:index')
    query = params.urlencode()
    return redirect(f'{url}?{query}' if query else url)
