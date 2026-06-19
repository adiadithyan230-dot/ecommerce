from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import pandas as pd

from analytics.data_loader import load_data
from analytics.analytics_engine import filter_dataframe, calculate_kpis, generate_forecast
from analytics import chart_engine

class KPIApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = load_data()
        if df is None or df.empty:
            return Response({"error": "No active dataset loaded"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get request params to filter
        filters = {
            'date_start': request.query_params.get('date_start'),
            'date_end': request.query_params.get('date_end'),
            'category': request.query_params.getlist('category') or None,
            'region': request.query_params.getlist('region') or None,
            'payment_method': request.query_params.getlist('payment_method') or None,
            'order_status': request.query_params.getlist('order_status') or None,
        }
        filtered_df = filter_dataframe(df, filters)
        kpis = calculate_kpis(filtered_df)
        return Response(kpis)

class ChartApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = load_data()
        if df is None or df.empty:
            return Response({"error": "No active dataset loaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        filters = {
            'date_start': request.query_params.get('date_start'),
            'date_end': request.query_params.get('date_end'),
            'category': request.query_params.getlist('category') or None,
            'region': request.query_params.getlist('region') or None,
        }
        filtered_df = filter_dataframe(df, filters)
        
        import json
        charts = {
            'monthly_trend': json.loads(chart_engine.generate_monthly_sales_trend(filtered_df) or '{}'),
            'category_rev': json.loads(chart_engine.generate_revenue_by_category(filtered_df) or '{}'),
            'region_rev': json.loads(chart_engine.generate_revenue_by_region(filtered_df) or '{}'),
            'payment_methods': json.loads(chart_engine.generate_payment_methods(filtered_df) or '{}'),
        }
        return Response(charts)

class OrdersApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = load_data()
        if df is None or df.empty:
            return Response({"error": "No active dataset loaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        filters = {
            'product_search': request.query_params.get('product_search'),
            'category': request.query_params.getlist('category') or None,
        }
        filtered_df = filter_dataframe(df, filters)
        
        limit = int(request.query_params.get('limit', 50))
        orders = filtered_df.head(limit).to_dict(orient='records')
        return Response(orders)

class ForecastApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = load_data()
        if df is None or df.empty:
            return Response({"error": "No active dataset loaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        forecast = generate_forecast(df)
        return Response(forecast)

class ReportsApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        df = load_data()
        if df is None or df.empty:
            return Response({"error": "No active dataset loaded"}, status=status.HTTP_400_BAD_REQUEST)
            
        filters = {
            'date_start': request.query_params.get('date_start'),
            'date_end': request.query_params.get('date_end'),
        }
        filtered_df = filter_dataframe(df, filters)
        kpis = calculate_kpis(filtered_df)
        
        from analytics.insight_engine import generate_insights
        insights = generate_insights(filtered_df, kpis)
        
        report_data = {
            "summary": "Executive Analytics Report",
            "kpis": kpis,
            "insights": insights,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        return Response(report_data)
