from django.urls import path
from . import views

urlpatterns = [
    path('my-bookings/', views.my_booking_history, name='api-my-bookings'),
    path('admin/all-bookings/', views.admin_all_bookings, name='api-admin-all-bookings'),
    path('admin/stats/', views.admin_stats, name='api-admin-stats'),
]
