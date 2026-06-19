from django.db import models
from django.conf import settings

class Dataset(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    row_count = models.IntegerField(null=True, blank=True)
    column_count = models.IntegerField(null=True, blank=True)
    quality_score = models.PositiveSmallIntegerField(default=0)
    quality_grade = models.CharField(max_length=20, default='Not scored')
    is_active = models.BooleanField(default=False)
    summary = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Mark all other datasets as inactive
            Dataset.objects.filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.uploaded_at.strftime('%Y-%m-%d %H:%M')})"
