import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json

def get_chart_theme_colors():
    return {
        'primary': '#4361ee',
        'secondary': '#3f37c9',
        'success': '#4cc9f0',
        'info': '#4895ef',
        'warning': '#f72585',
        'danger': '#b5179e',
        'bg_dark': '#1e1e2f',
        'text_dark': '#ffffff',
        'grid_dark': '#2d2d44'
    }

def generate_monthly_sales_trend(df):
    date_col = [col for col in df.columns if 'date' in col]
    if not date_col or 'revenue' not in df.columns or df.empty:
        return None
    col = date_col[0]
    
    # Pre-process dates
    df_copy = df.copy()
    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
    df_copy.dropna(subset=[col], inplace=True)
    
    monthly = df_copy.groupby(df_copy[col].dt.to_period('M'))['revenue'].sum().reset_index()
    monthly[col] = monthly[col].astype(str)
    
    colors = get_chart_theme_colors()
    fig = px.area(monthly, x=col, y='revenue', 
                  title="Monthly Revenue Trend",
                  labels={col: 'Month', 'revenue': 'Revenue (Rs)'},
                  color_discrete_sequence=[colors['primary']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor='#e9ecef')
    fig.update_yaxes(showgrid=True, gridcolor='#e9ecef')
    return fig.to_json()

def generate_revenue_by_category(df):
    if 'category' not in df.columns or 'revenue' not in df.columns or df.empty:
        return None
    
    cat_data = df.groupby('category')['revenue'].sum().reset_index()
    colors = get_chart_theme_colors()
    
    fig = px.bar(cat_data, x='category', y='revenue',
                 title="Revenue by Category",
                 labels={'category': 'Category', 'revenue': 'Revenue (Rs)'},
                 color='revenue',
                 color_continuous_scale=[colors['primary'], colors['success']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#e9ecef')
    return fig.to_json()

def generate_revenue_by_region(df):
    if 'region' not in df.columns or 'revenue' not in df.columns or df.empty:
        return None
    
    region_data = df.groupby('region')['revenue'].sum().reset_index()
    colors = get_chart_theme_colors()
    
    fig = px.pie(region_data, values='revenue', names='region',
                 title="Revenue by Region",
                 color_discrete_sequence=[colors['primary'], colors['secondary'], colors['info'], colors['success']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig.to_json()

def generate_payment_methods(df):
    if 'payment_method' not in df.columns or df.empty:
        return None
    
    pay_data = df.groupby('payment_method').size().reset_index(name='orders')
    colors = get_chart_theme_colors()
    
    fig = px.pie(pay_data, values='orders', names='payment_method',
                 title="Payment Methods",
                 hole=0.4,
                 color_discrete_sequence=[colors['primary'], colors['info'], colors['warning'], colors['danger']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig.to_json()

def generate_order_status(df):
    if 'order_status' not in df.columns or df.empty:
        return None
    
    status_data = df.groupby('order_status').size().reset_index(name='count')
    colors = get_chart_theme_colors()
    
    fig = px.bar(status_data, x='order_status', y='count',
                 title="Order Status Distribution",
                 labels={'order_status': 'Status', 'count': 'Orders Count'},
                 color_discrete_sequence=[colors['secondary']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor='#e9ecef')
    return fig.to_json()

def generate_top_products(df):
    if 'product' not in df.columns or 'revenue' not in df.columns or df.empty:
        return None
    
    top_prod = df.groupby('product')['revenue'].sum().reset_index()
    top_prod = top_prod.sort_values(by='revenue', ascending=False).head(10)
    
    colors = get_chart_theme_colors()
    fig = px.bar(top_prod, x='revenue', y='product',
                 orientation='h',
                 title="Top 10 Products by Revenue",
                 labels={'revenue': 'Revenue (Rs)', 'product': 'Product'},
                 color_discrete_sequence=[colors['info']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis={'categoryorder': 'total ascending'}
    )
    fig.update_xaxes(showgrid=True, gridcolor='#e9ecef')
    fig.update_yaxes(showgrid=False)
    return fig.to_json()

def generate_daily_revenue(df):
    date_col = [col for col in df.columns if 'date' in col]
    if not date_col or 'revenue' not in df.columns or df.empty:
        return None
    col = date_col[0]
    
    df_copy = df.copy()
    df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
    df_copy.dropna(subset=[col], inplace=True)
    
    daily = df_copy.groupby(df_copy[col].dt.date)['revenue'].sum().reset_index()
    daily[col] = daily[col].astype(str)
    
    colors = get_chart_theme_colors()
    fig = px.line(daily, x=col, y='revenue', 
                  title="Daily Revenue Trend",
                  labels={col: 'Date', 'revenue': 'Revenue (Rs)'},
                  color_discrete_sequence=[colors['primary']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor='#e9ecef')
    fig.update_yaxes(showgrid=True, gridcolor='#e9ecef')
    return fig.to_json()

def generate_revenue_heatmap(df):
    if 'region' not in df.columns or 'category' not in df.columns or 'revenue' not in df.columns or df.empty:
        return None
        
    pivot = df.pivot_table(index='region', columns='category', values='revenue', aggfunc='sum').fillna(0)
    
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.tolist(),
        y=pivot.index.tolist(),
        colorscale='Viridis',
        hoverongaps=False
    ))
    
    fig.update_layout(
        title="Revenue Heatmap (Region vs Category)",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40)
    )
    return fig.to_json()

def generate_forecast_chart(forecast_data):
    if not forecast_data:
        return None
        
    df_fc = pd.DataFrame(forecast_data)
    colors = get_chart_theme_colors()
    
    fig = px.line(df_fc, x='period', y='predicted_revenue', markers=True,
                  title="3-Month Revenue Forecast",
                  labels={'period': 'Forecast Period', 'predicted_revenue': 'Predicted Revenue (Rs)'},
                  color_discrete_sequence=[colors['warning']])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#6c757d',
        margin=dict(l=40, r=40, t=40, b=40),
        hovermode="x unified"
    )
    fig.update_xaxes(showgrid=True, gridcolor='#e9ecef')
    fig.update_yaxes(showgrid=True, gridcolor='#e9ecef')
    return fig.to_json()
