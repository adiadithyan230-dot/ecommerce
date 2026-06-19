from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Custom HTML-based Admin Dashboard
    path('admin-dashboard/', views.AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin-dashboard/users/<int:pk>/role/', views.UpdateUserRoleView.as_view(), name='update_user_role'),
    path('admin-dashboard/users/<int:pk>/toggle-status/', views.ToggleUserStatusView.as_view(), name='toggle_user_status'),
    path('admin-dashboard/users/<int:pk>/delete/', views.DeleteUserView.as_view(), name='delete_user'),
    path('admin-dashboard/datasets/<int:pk>/delete/', views.DeleteDatasetView.as_view(), name='delete_dataset'),
]
