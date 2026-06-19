import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.linear_model import LinearRegression

def filter_dataframe(df, filters=None):
    """
    Applies filters to the DataFrame dynamically.
    """
    if df is None or df.empty:
        return df
        
    filtered_df = df.copy()
    
    if not filters:
        return filtered_df
        
    # Date Range Filter
    date_col = [col for col in filtered_df.columns if 'date' in col]
    if date_col:
        col = date_col[0]
        # Ensure date format
        if not pd.api.types.is_datetime64_any_dtype(filtered_df[col]):
            filtered_df[col] = pd.to_datetime(filtered_df[col], errors='coerce')
        
        start_date = filters.get('date_start')
        end_date = filters.get('date_end')
        
        if start_date:
            filtered_df = filtered_df[filtered_df[col] >= pd.to_datetime(start_date)]
        if end_date:
            filtered_df = filtered_df[filtered_df[col] <= pd.to_datetime(end_date)]

    # Category Filter
    if 'category' in filtered_df.columns and filters.get('category'):
        cats = filters.get('category')
        if isinstance(cats, str):
            cats = [cats]
        filtered_df = filtered_df[filtered_df['category'].isin(cats)]
        
    # Region Filter
    if 'region' in filtered_df.columns and filters.get('region'):
        regs = filters.get('region')
        if isinstance(regs, str):
            regs = [regs]
        filtered_df = filtered_df[filtered_df['region'].isin(regs)]
        
    # Payment Method Filter
    if 'payment_method' in filtered_df.columns and filters.get('payment_method'):
        methods = filters.get('payment_method')
        if isinstance(methods, str):
            methods = [methods]
        filtered_df = filtered_df[filtered_df['payment_method'].isin(methods)]
        
    # Order Status Filter
    if 'order_status' in filtered_df.columns and filters.get('order_status'):
        status = filters.get('order_status')
        if isinstance(status, str):
            status = [status]
        filtered_df = filtered_df[filtered_df['order_status'].isin(status)]

    # Revenue Range Filter
    if 'revenue' in filtered_df.columns:
        rev_min = filters.get('revenue_min')
        rev_max = filters.get('revenue_max')
        if rev_min is not None and rev_min != '':
            filtered_df = filtered_df[filtered_df['revenue'] >= float(rev_min)]
        if rev_max is not None and rev_max != '':
            filtered_df = filtered_df[filtered_df['revenue'] <= float(rev_max)]
            
    # Search Product Filter
    if 'product' in filtered_df.columns and filters.get('product_search'):
        search = filters.get('product_search').lower().strip()
        if search:
            filtered_df = filtered_df[filtered_df['product'].str.lower().str.contains(search, na=False)]
            
    return filtered_df

def calculate_kpis(df):
    """
    Computes SaaS dashboard KPI metrics including advanced business intelligence indicators.
    """
    kpis = {
        'total_revenue': 0.0,
        'total_orders': 0,
        'aov': 0.0,
        'top_region': 'N/A',
        'top_category': 'N/A',
        'monthly_growth': 0.0,
        'cancellation_rate': 0.0,
        'return_rate': 0.0,
        'returning_customer_rate': 0.0,
        'gross_profit': 0.0,
        'profit_margin': 0.0,
        'avg_basket_size': 0.0,
        'best_sales_month': 'N/A',
        'worst_sales_month': 'N/A',
    }
    
    if df is None or df.empty:
        return kpis
        
    # Ensure correct columns exist
    cols = df.columns
    
    # 1. Total Revenue
    if 'revenue' in cols:
        kpis['total_revenue'] = float(df['revenue'].sum())
        
    # 2. Total Orders
    if 'order_id' in cols:
        kpis['total_orders'] = int(df['order_id'].nunique())
    else:
        kpis['total_orders'] = len(df)
        
    # 3. Average Order Value
    if kpis['total_orders'] > 0:
        kpis['aov'] = kpis['total_revenue'] / kpis['total_orders']
        
    # 4. Top Region
    if 'region' in cols and 'revenue' in cols:
        region_rev = df.groupby('region')['revenue'].sum()
        if not region_rev.empty:
            kpis['top_region'] = region_rev.idxmax()
            
    # 5. Top Category
    if 'category' in cols and 'revenue' in cols:
        cat_rev = df.groupby('category')['revenue'].sum()
        if not cat_rev.empty:
            kpis['top_category'] = cat_rev.idxmax()
            
    # 6. Cancellation Rate
    if 'order_status' in cols:
        cancelled = df[df['order_status'].str.lower() == 'cancelled']
        kpis['cancellation_rate'] = (len(cancelled) / len(df)) * 100 if len(df) > 0 else 0.0
        
    # 7. Return Rate
    if 'order_status' in cols:
        returned = df[df['order_status'].str.lower() == 'returned']
        kpis['return_rate'] = (len(returned) / len(df)) * 100 if len(df) > 0 else 0.0

    # 8. Returning Customers
    if 'customer_name' in cols:
        customer_counts = df['customer_name'].value_counts()
        returning = (customer_counts > 1).sum()
        total_unique = len(customer_counts)
        kpis['returning_customer_rate'] = (returning / total_unique) * 100 if total_unique > 0 else 0.0

    # 9. Gross Profit (estimated as 30% margin if no cost column)
    if 'cost' in cols and 'revenue' in cols:
        kpis['gross_profit'] = float(df['revenue'].sum() - df['cost'].sum())
    elif 'revenue' in cols:
        kpis['gross_profit'] = float(df['revenue'].sum() * 0.30)

    # 10. Profit Margin %
    if kpis['total_revenue'] > 0:
        kpis['profit_margin'] = (kpis['gross_profit'] / kpis['total_revenue']) * 100

    # 11. Average Basket Size (avg items per order)
    if 'quantity' in cols:
        if 'order_id' in cols:
            basket = df.groupby('order_id')['quantity'].sum()
            kpis['avg_basket_size'] = float(basket.mean()) if not basket.empty else 0.0
        else:
            kpis['avg_basket_size'] = float(df['quantity'].mean())

    # 12. Best & Worst Sales Month
    date_col = [col for col in cols if 'date' in col]
    if date_col and 'revenue' in cols:
        col = date_col[0]
        df_dates = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df_dates[col]):
            df_dates[col] = pd.to_datetime(df_dates[col], errors='coerce')
        df_dates.dropna(subset=[col], inplace=True)
        
        if not df_dates.empty:
            # Group by Month-Year
            monthly_sales = df_dates.groupby(df_dates[col].dt.to_period('M'))['revenue'].sum().sort_index()
            
            if not monthly_sales.empty:
                best_period = monthly_sales.idxmax()
                worst_period = monthly_sales.idxmin()
                kpis['best_sales_month'] = str(best_period)
                kpis['worst_sales_month'] = str(worst_period)
            
            # 13. Monthly Growth %
            if len(monthly_sales) >= 2:
                latest_month_rev = monthly_sales.iloc[-1]
                prev_month_rev = monthly_sales.iloc[-2]
                if prev_month_rev > 0:
                    kpis['monthly_growth'] = ((latest_month_rev - prev_month_rev) / prev_month_rev) * 100
                    
    return kpis

def generate_forecast(df, periods=3):
    """
    Performs sales forecasting for the next N months using a simple Linear Regression model.
    Also predicts demand for the top product and top category.
    """
    forecast_data = []
    
    date_col = [col for col in df.columns if 'date' in col]
    if not date_col or 'revenue' not in df.columns or df.empty:
        return forecast_data
        
    col = date_col[0]
    df_dates = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_dates[col]):
        df_dates[col] = pd.to_datetime(df_dates[col], errors='coerce')
    df_dates.dropna(subset=[col], inplace=True)
    
    if df_dates.empty:
        return forecast_data
        
    # Group by month for total revenue
    monthly_sales = df_dates.groupby(df_dates[col].dt.to_period('M'))['revenue'].sum().reset_index()
    monthly_sales['month_index'] = np.arange(len(monthly_sales))
    
    if len(monthly_sales) < 3:
        return forecast_data  # Need at least 3 months for a decent linear regression trend
        
    # Model for Revenue
    X = monthly_sales[['month_index']].values
    y_rev = monthly_sales['revenue'].values
    rev_model = LinearRegression()
    rev_model.fit(X, y_rev)
    
    # Model for Top Product Demand
    top_product = "N/A"
    prod_model = None
    if 'product' in df_dates.columns and 'quantity' in df_dates.columns:
        top_product = df_dates.groupby('product')['quantity'].sum().idxmax()
        prod_data = df_dates[df_dates['product'] == top_product].groupby(df_dates[col].dt.to_period('M'))['quantity'].sum().reindex(monthly_sales[col]).fillna(0).reset_index()
        y_prod = prod_data['quantity'].values
        prod_model = LinearRegression()
        prod_model.fit(X, y_prod)

    # Model for Top Category Growth
    top_category = "N/A"
    cat_model = None
    if 'category' in df_dates.columns:
        top_category = df_dates.groupby('category')['revenue'].sum().idxmax()
        cat_data = df_dates[df_dates['category'] == top_category].groupby(df_dates[col].dt.to_period('M'))['revenue'].sum().reindex(monthly_sales[col]).fillna(0).reset_index()
        y_cat = cat_data['revenue'].values
        cat_model = LinearRegression()
        cat_model.fit(X, y_cat)

    # Predict next periods
    last_index = monthly_sales['month_index'].max()
    last_period = monthly_sales[col].max()
    
    for i in range(1, periods + 1):
        next_index = last_index + i
        next_period = last_period + i
        
        pred_rev = max(0.0, float(rev_model.predict([[next_index]])[0]))
        pred_prod = max(0.0, float(prod_model.predict([[next_index]])[0])) if prod_model else 0.0
        pred_cat = max(0.0, float(cat_model.predict([[next_index]])[0])) if cat_model else 0.0
        
        forecast_data.append({
            'period': str(next_period),
            'predicted_revenue': round(pred_rev, 2),
            'top_product': top_product,
            'predicted_product_demand': int(round(pred_prod)),
            'top_category': top_category,
            'predicted_category_revenue': round(pred_cat, 2)
        })
        
    return forecast_data
