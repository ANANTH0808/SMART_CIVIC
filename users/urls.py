from django.urls import path
from .views import *

urlpatterns = [
    path('', home),
    path('userlogin/', user_login),
    path('adminlogin/', admin_login),
    path('register/', register),
    path('logout/', logout_view, name='logout'),
]