from django.urls import path
from . import views

urlpatterns = [
    path('', views.package_list, name='api-packages-list'),
    path('<int:pk>/', views.package_detail, name='api-packages-detail'),

    path('admin/', views.admin_package_list_create, name='api-admin-packages-list-create'),
    path('admin/<int:pk>/', views.admin_package_detail, name='api-admin-packages-detail'),
    path('admin/<int:pk>/status/<str:new_status>/', views.admin_package_set_status, name='api-admin-packages-status'),

    path('bookings/', views.booking_list_create, name='api-package-bookings-list-create'),
    path('bookings/<int:pk>/', views.booking_detail, name='api-package-bookings-detail'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='api-package-bookings-cancel'),
    path('bookings/<int:pk>/status/<str:new_status>/', views.booking_set_status, name='api-package-bookings-status'),
]
