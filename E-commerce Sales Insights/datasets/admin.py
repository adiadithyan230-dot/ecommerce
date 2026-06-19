from django.contrib import admin
from .models import Dataset

class DatasetAdmin(admin.ModelAdmin):
    list_display = ('name', 'uploaded_at', 'uploaded_by', 'row_count', 'column_count', 'is_active')
    list_filter = ('is_active', 'uploaded_at')
    search_fields = ('name', 'uploaded_by__username')
    ordering = ('-uploaded_at',)

admin.site.register(Dataset, DatasetAdmin)
