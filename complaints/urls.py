from django.urls import path
from .views import (
    user_dashboard, create_ui, detail, add_comment,
    update_status, kanban, notifications, profile,
    admin_dashboard, edit_profile, delete_complaint, admin_login,
)

urlpatterns = [
    path('dashboard/', user_dashboard, name='dashboard'),
    path('create-ui/', create_ui, name='create-complaint'),
    path('detail/<int:id>/', detail, name='complaint-detail'),
    path('comment/<int:id>/', add_comment, name='add-comment'),
    path('update/<int:id>/', update_status, name='update-status'),
    path('kanban/', kanban, name='kanban'),
    path('notifications/', notifications, name='notifications'),
    path('profile/', profile, name='profile'),
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),
    path('edit-profile/', edit_profile, name='edit-profile'),
    path('delete/<int:id>/', delete_complaint, name='delete-complaint'),
    path('admin-login/', admin_login, name='complaints-admin-login'),
]
