from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def admin_dashboard(request):
    return render(request, 'dashboard/admin_dashboard.html')

@login_required
def journalist_dashboard(request):
    return render(request, 'dashboard/journalist_dashboard.html')

@login_required
def advertiser_dashboard(request):
    return render(request, 'dashboard/advertiser_dashboard.html')
