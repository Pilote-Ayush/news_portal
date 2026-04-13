from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('journalist-dashboard/', views.journalist_dashboard, name='journalist_dashboard'),
    path('advertiser-dashboard/', views.advertiser_dashboard, name='advertiser_dashboard'),
]