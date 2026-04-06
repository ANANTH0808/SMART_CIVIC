from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User

# HOME
def home(request):
    return render(request, 'home.html')


# USER LOGIN
def user_login(request):
    if request.method == "POST":
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user:
            login(request, user)
            return redirect('/complaints/dashboard/')
    return render(request, 'user_login.html')


# ADMIN LOGIN
def admin_login(request):
    if request.method == "POST":
        user = authenticate(
            username=request.POST['username'],
            password=request.POST['password']
        )
        if user and user.is_superuser:
            login(request, user)
            return redirect('/complaints/admin-dashboard/')
    return render(request, 'admin_login.html')


# REGISTER
def register(request):
    if request.method == "POST":
        User.objects.create_user(
            username=request.POST['username'],
            password=request.POST['password']
        )
        return redirect('/userlogin/')
    return render(request, 'register.html')


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect('/')