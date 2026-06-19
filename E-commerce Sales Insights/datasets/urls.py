from django.urls import path
from . import views

app_name = 'datasets'

urlpatterns = [
    path('', views.DatasetListView.as_view(), name='list'),
    path('upload/', views.DatasetUploadView.as_view(), name='upload'),
    path('activate/<int:pk>/', views.activate_dataset, name='activate'),
    path('preview/<int:pk>/', views.preview_dataset, name='preview'),
    path('delete/<int:pk>/', views.DatasetDeleteView.as_view(), name='delete'),
]
