from django.urls import path
from .views import *

urlpatterns = [

    # 👤 USER
    path('dashboard/', user_dashboard, name='user-dashboard'),

    # 🛠 ADMIN
    path('admin-dashboard/', admin_dashboard, name='admin-dashboard'),

    # 🔄 UPDATE (ADMIN)
    path('update/<int:id>/', update_complaint_ui, name='update-complaint'),

    # 📄 FILTER PAGES
    path('pending/', pending_page),
    path('progress/', progress_page),
    path('resolved/', resolved_page),
    path('create-ui/', create_complaint, name='create-complaint'),
    # 📄 DETAIL
    path('detail/<int:id>/', complaint_detail),
]