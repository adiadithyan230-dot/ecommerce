"""
AI-Free Insight Generator — Rule-based business intelligence insights.
Generates human-readable insights from KPIs and DataFrame analysis without AI/ML.
"""
import pandas as pd


def generate_insights(df, kpis):
    """
    Produces categorized, rule-based executive insights with severity levels.
    Returns a dict with categories: Revenue, Product, Customer, Risk.
    Each item has 'text' and 'severity' (good, warning, critical).
    """
    insights = {
        'Revenue Insights': [],
        'Product Insights': [],
        'Customer Insights': [],
        'Risk Alerts': []
    }

    if df is None or df.empty or not kpis:
        insights['Risk Alerts'].append({
            'text': "No data available to generate insights.",
            'severity': "critical"
        })
        return insights

    cols = df.columns

    # --- Revenue Insights ---
    if kpis.get('total_revenue', 0) > 0:
        insights['Revenue Insights'].append({
            'text': f"Total revenue across all transactions is Rs {kpis['total_revenue']:,.2f} with {kpis['total_orders']:,} orders processed.",
            'severity': 'good'
        })

    if kpis.get('aov', 0) > 0:
        insights['Revenue Insights'].append({
            'text': f"The average order value is Rs {kpis['aov']:,.2f}.",
            'severity': 'good'
        })

    growth = kpis.get('monthly_growth', 0)
    if growth > 0:
        insights['Revenue Insights'].append({
            'text': f"Monthly revenue grew by {growth:.1f}% compared to the previous month.",
            'severity': 'good'
        })
    elif growth < 0:
        insights['Risk Alerts'].append({
            'text': f"Monthly revenue declined by {abs(growth):.1f}% compared to the previous month. Immediate attention is recommended.",
            'severity': 'critical'
        })

    margin = kpis.get('profit_margin', 0)
    if margin > 0:
        insights['Revenue Insights'].append({
            'text': f"Estimated profit margin is {margin:.1f}% with gross profit of Rs {kpis.get('gross_profit', 0):,.2f}.",
            'severity': 'good'
        })

    # --- Product Insights ---
    if kpis.get('top_category') and kpis['top_category'] != 'N/A':
        if 'category' in cols and 'revenue' in cols:
            cat_rev = df.groupby('category')['revenue'].sum().sort_values(ascending=False)
            if not cat_rev.empty:
                top_cat = cat_rev.index[0]
                top_val = cat_rev.iloc[0]
                pct = (top_val / kpis['total_revenue']) * 100 if kpis['total_revenue'] > 0 else 0
                insights['Product Insights'].append({
                    'text': f"The {top_cat} category leads revenue with Rs {top_val:,.2f} ({pct:.1f}% of total).",
                    'severity': 'good'
                })

    if 'product' in cols and 'revenue' in cols:
        prod_rev = df.groupby('product')['revenue'].sum()
        if not prod_rev.empty:
            top_product = prod_rev.idxmax()
            top_product_rev = prod_rev.max()
            insights['Product Insights'].append({
                'text': f"'{top_product}' is the best-selling product, generating Rs {top_product_rev:,.2f}.",
                'severity': 'good'
            })

    basket = kpis.get('avg_basket_size', 0)
    if basket > 0:
        insights['Product Insights'].append({
            'text': f"Customers are purchasing an average of {basket:.1f} items per order.",
            'severity': 'good'
        })

    # --- Customer Insights ---
    if kpis.get('top_region') and kpis['top_region'] != 'N/A':
        if 'region' in cols and 'revenue' in cols:
            reg_rev = df.groupby('region')['revenue'].sum().sort_values(ascending=False)
            if not reg_rev.empty:
                top_reg = reg_rev.index[0]
                top_val = reg_rev.iloc[0]
                insights['Customer Insights'].append({
                    'text': f"The {top_reg} region is the strongest market, contributing Rs {top_val:,.2f}.",
                    'severity': 'good'
                })

    retention = kpis.get('returning_customer_rate', 0)
    if retention >= 30:
        insights['Customer Insights'].append({
            'text': f"Customer retention is strong at {retention:.1f}%. Loyalty programs are highly effective.",
            'severity': 'good'
        })
    elif retention > 0:
        insights['Customer Insights'].append({
            'text': f"Only {retention:.1f}% of customers are returning. Consider post-purchase engagement to boost loyalty.",
            'severity': 'warning'
        })

    if 'payment_method' in cols:
        top_pay = df['payment_method'].value_counts()
        if not top_pay.empty:
            insights['Customer Insights'].append({
                'text': f"The preferred payment method is {top_pay.index[0]} ({top_pay.iloc[0]:,} transactions).",
                'severity': 'good'
            })

    # --- Risk Alerts ---
    cancel_rate = kpis.get('cancellation_rate', 0)
    if cancel_rate > 15:
        insights['Risk Alerts'].append({
            'text': f"High Cancellation Rate: {cancel_rate:.1f}% of orders are cancelled. Immediate investigation required.",
            'severity': 'critical'
        })
    elif cancel_rate > 8:
        insights['Risk Alerts'].append({
            'text': f"Cancellation rate is {cancel_rate:.1f}%. Consider reviewing inventory availability and checkout UX.",
            'severity': 'warning'
        })

    return_rate = kpis.get('return_rate', 0)
    if return_rate > 10:
        insights['Risk Alerts'].append({
            'text': f"High Return Rate: {return_rate:.1f}% of items are being returned. Quality control review is strongly advised.",
            'severity': 'critical'
        })
    elif return_rate > 5:
        insights['Risk Alerts'].append({
            'text': f"Return rate is {return_rate:.1f}%. Ensure product descriptions match the physical items.",
            'severity': 'warning'
        })

    if 'region' in cols and 'order_status' in cols:
        region_cancel = df[df['order_status'].str.lower() == 'cancelled'].groupby('region').size()
        region_totals = df.groupby('region').size()
        region_cancel_rate = ((region_cancel / region_totals) * 100).dropna().sort_values(ascending=False)
        if not region_cancel_rate.empty:
            worst_region = region_cancel_rate.index[0]
            worst_rate = region_cancel_rate.iloc[0]
            if worst_rate > 15:
                insights['Risk Alerts'].append({
                    'text': f"{worst_region} region is experiencing an abnormal cancellation rate of {worst_rate:.1f}%.",
                    'severity': 'critical'
                })

    # Filter out empty categories
    return {k: v for k, v in insights.items() if v}
