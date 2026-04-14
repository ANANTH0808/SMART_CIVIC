from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import HttpResponseForbidden
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Complaint, Comment, Notification

VALID_STATUSES = {'pending', 'inprogress', 'resolved'}

KEYWORDS = {
    "water": ["water", "leak", "pipe"],
    "road": ["road", "pothole", "street"],
    "sanitation": ["garbage", "waste", "trash"],
}

PAGE_SIZE = 10   # complaints per page on dashboards


def _auto_category(desc: str) -> str:
    """Classify a complaint description into a category."""
    desc_lower = desc.lower()
    for category, words in KEYWORDS.items():
        if any(word in desc_lower for word in words):
            return category
    return "general"


# ================= USER DASHBOARD =================
@login_required
def user_dashboard(request):
    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')

    # Single aggregated query instead of 5 separate ones
    base_qs = Complaint.objects.filter(user=request.user)
    stats = base_qs.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        progress=Count('id', filter=Q(status='inprogress')),
        resolved=Count('id', filter=Q(status='resolved')),
    )

    status_filter = request.GET.get('status')
    complaints = base_qs
    if status_filter in VALID_STATUSES:
        complaints = complaints.filter(status=status_filter)

    paginator = Paginator(complaints, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,
        'complaints': page_obj,   # keep template variable name unchanged
        **stats,
        'active_filter': status_filter,
    })


# ================= ADMIN DASHBOARD =================
@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('/complaints/dashboard/')

    # select_related('user') avoids one DB hit per complaint row
    all_qs = Complaint.objects.select_related('user')
    stats = all_qs.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(status='pending')),
        progress=Count('id', filter=Q(status='inprogress')),
        resolved=Count('id', filter=Q(status='resolved')),
    )

    paginator = Paginator(all_qs, PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'admin_dashboard.html', {
        'page_obj': page_obj,
        'complaints': page_obj,   # keep template variable name unchanged
        **stats,
    })


# ================= CREATE COMPLAINT =================
@login_required
def create_ui(request):
    if request.method == "POST":
        title = request.POST.get('title', '').strip()
        desc = request.POST.get('desc', '').strip()
        location = request.POST.get('location', '').strip()

        if not title or not desc or not location:
            return render(request, 'create.html', {
                'error': 'Title, description, and location are required.'
            })

        lat_raw = request.POST.get('latitude', '').strip()
        lng_raw = request.POST.get('longitude', '').strip()
        try:
            latitude = float(lat_raw) if lat_raw else None
            longitude = float(lng_raw) if lng_raw else None
        except ValueError:
            latitude = longitude = None

        Complaint.objects.create(
            user=request.user,
            title=title,
            desc=desc,
            location=location,
            latitude=latitude,
            longitude=longitude,
            image=request.FILES.get('image'),
            category=_auto_category(desc),
        )
        return redirect('/complaints/dashboard/')

    return render(request, 'create.html')


# ================= DETAIL PAGE =================
@login_required
def detail(request, id):
    c = get_object_or_404(Complaint.objects.select_related('user'), id=id)
    comments = c.comments.select_related('user').all()   # uses related_name

    return render(request, 'detail.html', {'c': c, 'comments': comments})


# ================= ADD COMMENT =================
@login_required
def add_comment(request, id):
    if request.method == "POST":
        text = request.POST.get('text', '').strip()
        if text:
            complaint = get_object_or_404(Complaint, id=id)
            Comment.objects.create(complaint=complaint, user=request.user, text=text)
    return redirect(f'/complaints/detail/{id}/')


# ================= UPDATE STATUS =================
@login_required
def update_status(request, id):
    c = get_object_or_404(Complaint, id=id)

    # Only the admin (superuser) may change status
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only admins can update complaint status.")

    if request.method == "POST":
        new_status = request.POST.get('status')
        if new_status in VALID_STATUSES:
            c.status = new_status
            c.save(update_fields=['status'])   # only update the status column

            Notification.objects.create(
                user=c.user,
                message=f'Your complaint "{c.title}" is now {c.get_status_display()}.',
            )

    return redirect('/complaints/admin-dashboard/')


# ================= DELETE =================
@login_required
def delete_complaint(request, id):
    c = get_object_or_404(Complaint, id=id)

    if request.user != c.user and not request.user.is_superuser:
        return HttpResponseForbidden("You cannot delete this complaint.")

    c.delete()

    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')
    return redirect('/complaints/dashboard/')


# ================= KANBAN =================
@login_required
def kanban(request):
    # One query, split in Python — much faster than three separate DB calls
    all_complaints = list(Complaint.objects.select_related('user').all())
    return render(request, 'kanban.html', {
        'pending':  [c for c in all_complaints if c.status == 'pending'],
        'progress': [c for c in all_complaints if c.status == 'inprogress'],
        'resolved': [c for c in all_complaints if c.status == 'resolved'],
    })


# ================= NOTIFICATIONS =================
@login_required
def notifications(request):
    notes = Notification.objects.filter(user=request.user)

    # Mark all unread as read when the page is opened
    notes.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications.html', {'notes': notes})


# ================= PROFILE =================
@login_required
def profile(request):
    return render(request, 'profile.html', {
        'user': request.user,
        'total': Complaint.objects.filter(user=request.user).count(),
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
                request.user.save(update_fields=['username', 'email'])
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


# ================= JWT LOGIN API =================
@api_view(['POST'])
def login_api(request):
    user = authenticate(
        username=request.data.get('username'),
        password=request.data.get('password'),
    )
    if user:
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    return Response({'error': 'Invalid credentials'}, status=401)
