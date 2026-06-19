from django.urls import path

from . import views

app_name = 'ai_insights'

urlpatterns = [
    path('generate/', views.generate_insight, name='generate'),
    path('history/', views.history, name='history'),
]
