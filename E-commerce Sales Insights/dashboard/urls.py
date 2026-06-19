from django.urls import path
from . import views
from . import api_views

app_name = 'dashboard'

urlpatterns = [
    # Template Views
    path('', views.index, name='index'),
    path('forecast/', views.forecast_view, name='forecast'),
    path('export/<str:format_type>/', views.export_report, name='export'),
    path('filters/save/', views.save_filter_view, name='save_filter'),
    
    # Presentation Docs Views
    path('docs/about/', views.about_view, name='about'),
    path('docs/methodology/', views.methodology_view, name='methodology'),
    path('docs/dataset/', views.dataset_info_view, name='dataset_info'),
    path('docs/flow/', views.flow_view, name='flow'),
    path('docs/viva/', views.viva_view, name='viva'),
    
    # REST API Views
    path('api/kpis/', api_views.KPIApiView.as_view(), name='api_kpis'),
    path('api/charts/', api_views.ChartApiView.as_view(), name='api_charts'),
    path('api/orders/', api_views.OrdersApiView.as_view(), name='api_orders'),
    path('api/forecast/', api_views.ForecastApiView.as_view(), name='api_forecast'),
    path('api/reports/', api_views.ReportsApiView.as_view(), name='api_reports'),
]
