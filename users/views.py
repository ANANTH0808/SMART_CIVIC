from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction


def _role_redirect(user):
    """Return the correct post-login URL based on user role."""
    if user.is_superuser:
        return '/complaints/admin-dashboard/'
    return '/complaints/dashboard/'


# HOME
def home(request):
    return render(request, 'home.html')


# MAIN LOGIN (replaces Django's LoginView — role-aware)
def login_view(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect(_role_redirect(user))
        else:
            error = "Invalid username or password."
    return render(request, 'login.html', {'error': error})


# USER LOGIN (citizen-facing portal)
def user_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect(_role_redirect(user))
        else:
            error = "Invalid username or password."
    return render(request, 'user_login.html', {'error': error})


# ADMIN LOGIN
def admin_login(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user and user.is_superuser:
            login(request, user)
            return redirect('/complaints/admin-dashboard/')
        else:
            error = "Invalid admin credentials."
    return render(request, 'admin_login.html', {'error': error})


# REGISTER
def register(request):
    error = None
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        if not username or not password:
            error = "Username and password are required."
        else:
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                    )
                return redirect('/login/')
            except IntegrityError:
                error = "Username already taken. Please choose another."

    return render(request, 'register.html', {'error': error})


# LOGOUT
def logout_view(request):
    logout(request)
    return redirect('/')
