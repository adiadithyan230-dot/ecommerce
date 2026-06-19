from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'user_id', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Profile Info', {'fields': ('user_id', 'role', 'bio', 'location')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Profile Info', {'fields': ('role', 'bio', 'location')}),
    )
    search_fields = ('username', 'email', 'user_id')
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
