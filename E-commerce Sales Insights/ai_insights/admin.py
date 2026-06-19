from django.contrib import admin

from .models import AIInsight


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'created_by', 'model_name', 'short_preview')
    list_filter = ('model_name', 'created_at')
    search_fields = ('generated_text', 'created_by__username', 'model_name')
    readonly_fields = ('created_at',)

    def short_preview(self, obj):
        return obj.preview

    short_preview.short_description = 'Insight Preview'
