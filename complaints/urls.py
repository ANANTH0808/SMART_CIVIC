from django.urls import path
from .views import *

urlpatterns = [
    path('dashboard/', user_dashboard),
    path('create-ui/', create_ui, name='create-complaint'),
    path('detail/<int:id>/', detail),
    path('comment/<int:id>/', add_comment),

    # ✅ ONLY ONE UPDATE
    path('update/<int:id>/', update_status, name='update-status'),

    path('kanban/', kanban),
    path('notifications/', notifications),
    path('profile/', profile, name='profile'),
    path('admin-dashboard/', admin_dashboard),
    path('edit-profile/', edit_profile, name='edit-profile'),
    path('delete/<int:id>/', delete_complaint, name='delete-complaint'),
]