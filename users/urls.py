from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView
urlpatterns = [
    
    path('register/', register,name='register'),
    path('', home,name='home'),
    path('user-login/', user_login,name='user-login'),
    path('admin-login/', admin_login,name='admin-login'),

    
    # path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('logout/', logout_view, name='logout'),
]