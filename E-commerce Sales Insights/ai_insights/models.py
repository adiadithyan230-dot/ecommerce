from django.conf import settings
from django.db import models


class AIInsight(models.Model):
    generated_text = models.TextField()
    model_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_insights',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        user = self.created_by.username if self.created_by else 'system'
        return f'{self.model_name} insight by {user} on {self.created_at:%Y-%m-%d %H:%M}'

    @property
    def preview(self):
        text = ' '.join(self.generated_text.split())
        return text[:180] + ('...' if len(text) > 180 else '')
