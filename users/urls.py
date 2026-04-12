from django.urls import path
from .views import home, user_login, admin_login, register, logout_view

urlpatterns = [
    path('', home, name='home'),
    path('userlogin/', user_login, name='user-login'),
    path('adminlogin/', admin_login, name='admin-login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout-view'),
]
