import pandas as pd
from django.core.cache.backends.base import memcache_key_warnings
from django.test import TestCase
from analytics.cleaning_engine import clean_data, detect_issues, validate_columns
from analytics.analytics_engine import calculate_kpis, generate_forecast
from analytics.data_loader import _dataset_cache_key
from analytics.insight_engine import generate_insights
from analytics.export_engine import export_csv

class AnalyticsEngineTests(TestCase):
    def setUp(self):
        # Create a sample DataFrame
        data = {
            'order_id': [1, 2, 3, 4],
            'customer_name': ['Alice', 'Bob', 'Alice', 'Charlie'],
            'product': ['Laptop', 'Mouse', 'Keyboard', 'Laptop'],
            'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics'],
            'region': ['North', 'South', 'North', 'East'],
            'quantity': [1, 2, 1, 1],
            'revenue': [1000.0, 50.0, 100.0, 1000.0],
            'payment_method': ['Credit Card', 'PayPal', 'Credit Card', 'Cash'],
            'order_status': ['Delivered', 'Cancelled', 'Delivered', 'Returned'],
            'order_date': ['2023-01-01', '2023-01-05', '2023-02-01', '2023-03-01']
        }
        self.df = pd.DataFrame(data)

    def test_clean_data(self):
        # Intentionally messy data
        messy_data = {
            'Order ID ': [1, 2],
            ' Product Name': ['A', 'B'],
            'TOTAL SALES': [100, 200]
        }
        messy_df = pd.DataFrame(messy_data)
        cleaned_df = clean_data(messy_df)
        self.assertIn('order_id', cleaned_df.columns)
        self.assertIn('product', cleaned_df.columns)
        self.assertIn('revenue', cleaned_df.columns)

    def test_detect_issues(self):
        # Create a new dataframe to avoid upcasting errors in pandas 3
        data = {
            'revenue': [100.0, -50.0, "Not a number", 200.0],
            'order_date': ['2023-01-01', 'invalid_date', '2023-01-03', '2023-01-04']
        }
        df_with_issues = pd.DataFrame(data)
        issues = detect_issues(df_with_issues)
        
        self.assertGreater(issues['negative_revenue_count'], 0)
        self.assertTrue(any("non-numeric" in warn for warn in issues['data_type_warnings']))
        self.assertGreater(issues['invalid_date_count'], 0)

    def test_validate_columns(self):
        is_valid, missing = validate_columns(self.df)
        self.assertTrue(is_valid)
        self.assertEqual(len(missing), 0)

    def test_calculate_kpis(self):
        kpis = calculate_kpis(self.df)
        self.assertEqual(kpis['total_revenue'], 2150.0)
        self.assertEqual(kpis['total_orders'], 4)
        self.assertEqual(kpis['top_category'], 'Electronics')
        self.assertEqual(kpis['top_region'], 'North')
        self.assertEqual(kpis['cancellation_rate'], 25.0)
        self.assertEqual(kpis['return_rate'], 25.0)

    def test_generate_insights(self):
        kpis = calculate_kpis(self.df)
        insights = generate_insights(self.df, kpis)
        self.assertIsInstance(insights, dict)
        self.assertGreater(len(insights), 0)
        all_insights = [item for items in insights.values() for item in items]
        self.assertTrue(any("Total revenue" in item["text"] for item in all_insights))

    def test_generate_forecast(self):
        forecast = generate_forecast(self.df, periods=1)
        self.assertIsInstance(forecast, list)

    def test_export_csv(self):
        csv_bytes = export_csv(self.df)
        self.assertTrue(len(csv_bytes) > 0)
        self.assertTrue(b'Alice' in csv_bytes)

    def test_dataset_cache_key_is_memcache_safe(self):
        filepath = (
            r"C:\Users\anton\Downloads\E-commerce Sales Insights"
            r"\E-commerce Sales Insights\media\datasets\ecommerce_data.csv"
        )

        cache_key = _dataset_cache_key(filepath)

        self.assertFalse(list(memcache_key_warnings(cache_key)))
        self.assertNotIn(filepath, cache_key)
