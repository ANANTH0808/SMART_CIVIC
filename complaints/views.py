from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.db import IntegrityError, transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Complaint, Comment, Notification

VALID_STATUSES = {'pending', 'inprogress', 'resolved'}


# ================= USER DASHBOARD =================
@login_required
def user_dashboard(request):
    # Admins must use the admin dashboard
    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')

    complaints = Complaint.objects.filter(user=request.user)

    status_filter = request.GET.get('status')
    if status_filter in VALID_STATUSES:
        complaints = complaints.filter(status=status_filter)

    all_complaints = Complaint.objects.filter(user=request.user)
    return render(request, 'dashboard.html', {
        'complaints': complaints,
        'total': all_complaints.count(),
        'pending': all_complaints.filter(status='pending').count(),
        'progress': all_complaints.filter(status='inprogress').count(),
        'resolved': all_complaints.filter(status='resolved').count(),
        'active_filter': status_filter,
    })


# ================= ADMIN DASHBOARD =================
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('/complaints/dashboard/')

    complaints = Complaint.objects.all()

    return render(request, 'admin_dashboard.html', {
        'complaints': complaints,
        'total': complaints.count(),
        'pending': complaints.filter(status='pending').count(),
        'progress': complaints.filter(status='inprogress').count(),
        'resolved': complaints.filter(status='resolved').count(),
    })


# ================= CREATE COMPLAINT =================
@login_required
def create_ui(request):
    if request.method == "POST":
        desc = request.POST.get('desc', '').lower()

        keywords = {
            "water": ["water", "leak", "pipe"],
            "road": ["road", "pothole", "street"],
            "sanitation": ["garbage", "waste", "trash"]
        }

        category = "general"
        for key, words in keywords.items():
            if any(word in desc for word in words):
                category = key
                break

        # Handle empty lat/lng strings from POST (map not clicked)
        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        latitude = float(lat_raw) if lat_raw else None
        longitude = float(lng_raw) if lng_raw else None

        Complaint.objects.create(
            user=request.user,
            title=request.POST.get('title', '').strip(),
            desc=request.POST.get('desc', '').strip(),
            location=request.POST.get('location', '').strip(),
            latitude=latitude,
            longitude=longitude,
            image=request.FILES.get('image'),
            category=category,
        )

        return redirect('/complaints/dashboard/')

    return render(request, 'create.html')


# ================= DETAIL PAGE =================
@login_required
def detail(request, id):
    c = get_object_or_404(Complaint, id=id)
    comments = Comment.objects.filter(complaint=c)

    return render(request, 'detail.html', {
        'c': c,
        'comments': comments
    })


# ================= ADD COMMENT =================
@login_required
def add_comment(request, id):
    if request.method == "POST":
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(
                complaint=get_object_or_404(Complaint, id=id),
                user=request.user,
                text=text,
            )

    return redirect(f'/complaints/detail/{id}/')


# ================= UPDATE STATUS =================
@login_required
def update_status(request, id):
    c = get_object_or_404(Complaint, id=id)

    if request.method == "POST":
        new_status = request.POST.get('status')
        if new_status in VALID_STATUSES:
            c.status = new_status
            c.save()

            Notification.objects.create(
                user=c.user,
                message=f"{c.title} → {c.status}"
            )

    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')
    return redirect('/complaints/dashboard/')


# ================= DELETE =================
@login_required
def delete_complaint(request, id):
    c = get_object_or_404(Complaint, id=id)

    if request.user == c.user or request.user.is_superuser:
        c.delete()

    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')
    return redirect('/complaints/dashboard/')


# ================= KANBAN =================
@login_required
def kanban(request):
    return render(request, 'kanban.html', {
        'pending': Complaint.objects.filter(status='pending'),
        'progress': Complaint.objects.filter(status='inprogress'),
        'resolved': Complaint.objects.filter(status='resolved'),
    })


# ================= NOTIFICATIONS =================
@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user).order_by('-created_at')

    return render(request, 'notifications.html', {
        'notes': notes
    })


# ================= PROFILE =================
@login_required
def profile(request):
    return render(request, 'profile.html', {
        'user': request.user,
        'total': Complaint.objects.filter(user=request.user).count()
    })


# ================= EDIT PROFILE =================
@login_required
def edit_profile(request):
    if request.method == "POST":
        new_username = request.POST.get('username', '').strip()
        new_email = request.POST.get('email', '').strip()

        if not new_username:
            return render(request, 'edit_profile.html', {'error': 'Username cannot be empty.'})

        try:
            with transaction.atomic():
                request.user.username = new_username
                request.user.email = new_email
                request.user.save()
            return redirect('/complaints/profile/')
        except IntegrityError:
            return render(request, 'edit_profile.html', {'error': 'That username is already taken.'})

    return render(request, 'edit_profile.html')


# ================= ADMIN LOGIN =================
def admin_login(request):
    error = None

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)

        if user and user.is_superuser:
            login(request, user)
            return redirect('/complaints/admin-dashboard/')
        else:
            error = "Invalid admin credentials"

    return render(request, 'admin_login.html', {'error': error})


# ================= JWT LOGIN =================
@api_view(['POST'])
def login_api(request):
    user = authenticate(
        username=request.data.get('username'),
        password=request.data.get('password')
    )

    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh)
        })

    return Response({'error': 'invalid credentials'}, status=401)
