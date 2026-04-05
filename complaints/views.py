from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.csrf import csrf_exempt

from .models import Complaint, Notification


# ================= USER DASHBOARD =================
@login_required
def user_dashboard(request):

    # 🚫 Admin should not access user dashboard
    if request.user.is_superuser:
        return redirect('/complaints/admin-dashboard/')

    complaints = Complaint.objects.filter(user=request.user)

    return render(request, 'dashboard.html', {
        'complaints': complaints,
        'total': complaints.count(),
        'pending': complaints.filter(status='pending').count(),
        'progress': complaints.filter(status='inprogress').count(),
        'resolved': complaints.filter(status='resolved').count(),
    })


# ================= ADMIN DASHBOARD =================
from django.db.models import Count
from datetime import datetime

@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return redirect('/complaints/dashboard/')

    complaints = Complaint.objects.all()

    # 🔍 SEARCH
    query = request.GET.get('q')
    if query:
        complaints = complaints.filter(title__icontains=query)

    # 📅 DATE FILTER
    date = request.GET.get('date')
    if date:
        complaints = complaints.filter(created_at__date=date)

    # 🔥 CATEGORY FIX (GENERAL DEFAULT)
    for c in complaints:
        if not c.category:
            c.category = "general"

    # 📊 CATEGORY COUNTS
    sanitation = Complaint.objects.filter(category='sanitation').count()
    road = Complaint.objects.filter(category='road').count()
    water = Complaint.objects.filter(category='water').count()
    general = Complaint.objects.filter(category__in=["", None, "general"]).count()

    return render(request, 'admin_dashboard.html', {
        'complaints': complaints,
        'total': complaints.count(),
        'pending': complaints.filter(status='pending').count(),
        'progress': complaints.filter(status='inprogress').count(),
        'resolved': complaints.filter(status='resolved').count(),

        'sanitation': sanitation,
        'road': road,
        'water': water,
        'general': general,
    })

# ================= UPDATE COMPLAINT (ADMIN ONLY) =================
@login_required
def update_complaint_ui(request, id):

    if not request.user.is_superuser:
        return redirect('/complaints/dashboard/')

    complaint = Complaint.objects.get(id=id)

    if request.method == "POST":
        complaint.status = request.POST.get('status')
        complaint.save()

    return redirect('/complaints/admin-dashboard/')


# ================= OTHER PAGES =================
@login_required
def pending_page(request):
    if request.user.is_superuser:
        complaints = Complaint.objects.filter(status='pending')
    else:
        complaints = Complaint.objects.filter(user=request.user)

    return render(request, 'pending.html', {'complaints': complaints})


@login_required
def progress_page(request):
    if request.user.is_superuser:
        complaints = Complaint.objects.filter(status='inprogress')
    else:
        complaints = Complaint.objects.filter(user=request.user)

    return render(request, 'progress.html', {'complaints': complaints})


@login_required
def resolved_page(request):
    if request.user.is_superuser:
        complaints = Complaint.objects.filter(status='resolved')
    else:
        complaints = Complaint.objects.filter(user=request.user)

    return render(request, 'resolved.html', {'complaints': complaints})


@login_required
def complaint_detail(request, id):
    complaint = Complaint.objects.get(id=id)

    if not request.user.is_superuser and complaint.user != request.user:
        return redirect('/complaints/dashboard/')

    return render(request, 'detail.html', {'c': complaint})

@login_required
def create_ui(request):
    if request.method == "POST":
        desc = request.POST.get('desc', '').lower()

        # 🔥 AUTO CATEGORY DETECTION
        if "garbage" in desc:
            category = "sanitation"
        elif "road" in desc:
            category = "road"
        elif "water" in desc or "leak" in desc:
            category = "water"
        else:
            category = "general"   # ✅ DEFAULT

        Complaint.objects.create(
            title=request.POST.get('title'),
            desc=request.POST.get('desc'),
            location=request.POST.get('location'),
            latitude=request.POST.get('latitude'),
            longitude=request.POST.get('longitude'),
            image=request.FILES.get('image'),
            status='pending',
            category=category,   # ✅ IMPORTANT
            user=request.user
        )

        return redirect('/complaints/dashboard/')

    return render(request, 'create.html')