import os
import shutil
import django

# Step 1: Run generate_data.py if data file doesn't exist
if not os.path.exists('data/ecommerce_data.csv'):
    print("Running generate_data.py to create initial dataset...")
    import generate_data

# Step 2: Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_insights.settings')
django.setup()

from django.contrib.auth import get_user_model
from datasets.models import Dataset
import pandas as pd
import json
from analytics.cleaning_engine import clean_data, detect_issues, validate_columns, calculate_quality_score

# Step 3: Create superuser if it doesn't exist
User = get_user_model()
username = 'admin'
email = 'admin@example.com'
password = 'admin'

if not User.objects.filter(username=username).exists():
    print(f"Creating superuser: {username}...")
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role='admin'
    )
    user.save()
    print("Superuser created successfully!")
else:
    print("Superuser already exists.")

# Step 4: Import the initial dataset into the media folder and register it in the DB
dest_dir = 'media/datasets'
os.makedirs(dest_dir, exist_ok=True)
dest_path = os.path.join(dest_dir, 'ecommerce_data.csv')

if not os.path.exists(dest_path):
    print("Copying ecommerce_data.csv to media/datasets...")
    shutil.copy('data/ecommerce_data.csv', dest_path)

if not Dataset.objects.filter(name='Demo E-commerce Dataset').exists():
    print("Registering demo dataset in the database...")
    # Load and clean to calculate metadata
    df = pd.read_csv(dest_path)
    issues = detect_issues(df)
    df_cleaned = clean_data(df)
    _is_valid, missing = validate_columns(df_cleaned)
    quality_score, quality_grade = calculate_quality_score(issues, missing)
    df_cleaned.to_csv(dest_path, index=False)
    
    admin_user = User.objects.get(username='admin')
    
    dataset = Dataset.objects.create(
        name='Demo E-commerce Dataset',
        file='datasets/ecommerce_data.csv',
        uploaded_by=admin_user,
        row_count=len(df_cleaned),
        column_count=len(df_cleaned.columns),
        quality_score=quality_score,
        quality_grade=quality_grade,
        summary=json.dumps(issues),
        is_active=True
    )
    dataset.save()
    print("Demo dataset registered and activated successfully!")
else:
    print("Demo dataset already registered.")
