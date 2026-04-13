from django.contrib import admin
from .models import News, Category, Notification

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'breaking', 'is_approved', 'created_at']

admin.site.register(Category)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']