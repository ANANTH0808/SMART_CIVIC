from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect


# REGISTER
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

def register(request):

    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        # ❌ Password mismatch
        if password != confirm_password:
            return render(request, 'register.html', {
                'error': 'Passwords do not match'
            })

        # ❌ User already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {
                'error': 'Username already exists'
            })

        # ✅ Create user
        User.objects.create_user(username=username, password=password)

        # 👉 Redirect to login
        return redirect('user-login')

    return render(request, 'register.html')

def home(request):
    return render(request,'home.html')

# USER LOGIN
def user_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user and not user.is_superuser:
            login(request, user)
            return redirect('/complaints/dashboard/')
        else:
            return render(request, 'user_login.html', {'error': 'Invalid user login'})

    return render(request, 'user_login.html')


# ADMIN LOGIN
def admin_login(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )

        if user and user.is_superuser:
            login(request, user)
            return redirect('/complaints/dashboard/')
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid admin login'})

    return render(request, 'admin_login.html')


# LOGOUT

def logout_view(request):
    logout(request)
    return redirect('home')