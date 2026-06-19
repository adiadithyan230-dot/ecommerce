import pandas as pd
import numpy as np

def clean_column_names(df):
    """
    Standardizes column names: strip spaces, lowercase, replace spaces/special chars with underscores.
    """
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r'[^\w\s]', '', regex=True)
        .str.replace(r'\s+', '_', regex=True)
    )
    return df

def detect_issues(df):
    """
    Identifies missing values, duplicates, wrong data types, invalid dates,
    and other data quality problems.
    """
    issues = {
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_count': int(df.duplicated().sum()),
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'data_type_warnings': [],
        'invalid_date_count': 0,
        'negative_revenue_count': 0,
    }

    # Check for columns that should be numeric but aren't
    numeric_expected = ['revenue', 'quantity', 'price', 'cost', 'total_sales', 'sales']
    for col in df.columns:
        col_lower = col.strip().lower().replace(' ', '_')
        if col_lower in numeric_expected:
            non_numeric = pd.to_numeric(df[col], errors='coerce').isna() & df[col].notna()
            count = int(non_numeric.sum())
            if count > 0:
                issues['data_type_warnings'].append(
                    f"Column '{col}' has {count} non-numeric values that should be numbers."
                )

    # Check for invalid dates
    date_cols = [col for col in df.columns if 'date' in col.lower()]
    for col in date_cols:
        parsed = pd.to_datetime(df[col], errors='coerce')
        invalid = parsed.isna() & df[col].notna()
        count = int(invalid.sum())
        issues['invalid_date_count'] += count
        if count > 0:
            issues['data_type_warnings'].append(
                f"Column '{col}' has {count} values that could not be parsed as valid dates."
            )

    # Check for negative revenue
    rev_cols = [col for col in df.columns if col.strip().lower() in ['revenue', 'total_sales', 'sales']]
    for col in rev_cols:
        numeric_vals = pd.to_numeric(df[col], errors='coerce')
        neg_count = int((numeric_vals < 0).sum())
        issues['negative_revenue_count'] += neg_count
        if neg_count > 0:
            issues['data_type_warnings'].append(
                f"Column '{col}' has {neg_count} negative values."
            )

    return issues

def clean_data(df):
    """
    Cleans dataset:
    - Fills or drops missing values.
    - Standardizes date formats.
    - Normalizes strings.
    """
    # Create copy to avoid modifying original view
    df = df.copy()
    
    # Standardize column names first
    df = clean_column_names(df)
    
    # Map raw column names to standardized ones
    rename_map = {
        'product_category': 'category',
        'product_name': 'product',
        'total_sales': 'revenue',
        'sales': 'revenue'
    }
    df.rename(columns=rename_map, inplace=True)
    
    # Drop completely empty columns
    df.dropna(how='all', axis=1, inplace=True)
    
    # Handle dates
    date_cols = [col for col in df.columns if 'date' in col]
    for col in date_cols:
        try:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        except Exception:
            pass
            
    # Handle missing values for numericals
    num_cols = df.select_dtypes(include=[np.number]).columns
    for col in num_cols:
        df[col] = df[col].fillna(df[col].median() if not df[col].isnull().all() else 0)
        
    # Handle missing values for categoricals
    cat_cols = df.select_dtypes(include=['object']).columns
    for col in cat_cols:
        df[col] = df[col].fillna('Unknown')
        
    # Drop duplicates
    df.drop_duplicates(inplace=True)
    
    return df

def validate_columns(df, required_fields=None):
    """
    Validates if required columns (or their cleaned counterparts) exist in the dataframe.
    """
    if required_fields is None:
        required_fields = [
            'order_id', 'customer_name', 'product', 'category', 'region', 
            'quantity', 'revenue', 'payment_method', 'order_status', 'order_date'
        ]
        
    cleaned_cols = set(df.columns)
    missing = [field for field in required_fields if field not in cleaned_cols]
    return len(missing) == 0, missing

def calculate_quality_score(issues, missing_required=None):
    """
    Produces a simple 0-100 quality score from validation and anomaly counts.
    """
    missing_required = missing_required or []
    total_rows = max(int(issues.get('total_rows') or 0), 1)
    missing_cells = sum(int(v or 0) for v in issues.get('missing_values', {}).values())
    duplicate_count = int(issues.get('duplicate_count') or 0)
    invalid_date_count = int(issues.get('invalid_date_count') or 0)
    negative_revenue_count = int(issues.get('negative_revenue_count') or 0)
    warning_count = len(issues.get('data_type_warnings') or [])

    score = 100
    score -= min(40, len(missing_required) * 12)
    score -= min(20, round((missing_cells / total_rows) * 8))
    score -= min(15, round((duplicate_count / total_rows) * 100))
    score -= min(15, round((invalid_date_count / total_rows) * 100))
    score -= min(15, round((negative_revenue_count / total_rows) * 100))
    score -= min(10, warning_count * 2)

    score = max(0, min(100, int(score)))
    if score >= 90:
        grade = 'Excellent'
    elif score >= 75:
        grade = 'Good'
    elif score >= 60:
        grade = 'Needs Review'
    else:
        grade = 'Poor'

    return score, grade
