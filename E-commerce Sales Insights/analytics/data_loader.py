import hashlib
import os

import pandas as pd
from django.core.cache import cache
from datasets.models import Dataset


def _dataset_cache_key(filepath):
    normalized_path = os.path.abspath(filepath)
    path_hash = hashlib.sha256(normalized_path.encode('utf-8')).hexdigest()
    return f"dataset_df_{path_hash}"


def get_active_dataset_path():
    try:
        active_dataset = Dataset.objects.filter(is_active=True).first()
        if active_dataset:
            return active_dataset.file.path
    except Exception:
        pass
    return None

def load_data(filepath=None, use_cache=True):
    if not filepath:
        filepath = get_active_dataset_path()
        if not filepath:
            return None

    cache_key = _dataset_cache_key(filepath)
    if use_cache:
        df_cached = cache.get(cache_key)
        if df_cached is not None:
            return df_cached

    try:
        df = pd.read_csv(filepath)
        if use_cache:
            cache.set(cache_key, df, timeout=3600)  # cache for 1 hour
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None
