from django.contrib import admin
from .models import Complaint, Comment, Notification


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'category', 'status', 'location', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'desc', 'location', 'user__username')
    list_editable = ('status',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('complaint', 'user', 'created_at')
    search_fields = ('text', 'user__username')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'message', 'created_at')
    search_fields = ('message', 'user__username')
