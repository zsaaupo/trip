from django.urls import path
from . import views

urlpatterns = [
    # Bus discovery + admin CRUD
    path('buses/', views.bus_list, name='api-buses-list'),
    path('buses/<int:pk>/', views.bus_detail, name='api-buses-detail'),
    path('admin/buses/', views.admin_bus_list_create, name='api-admin-buses-list-create'),
    path('admin/buses/<int:pk>/', views.admin_bus_detail, name='api-admin-buses-detail'),
    path('admin/buses/<int:pk>/status/<str:new_status>/', views.admin_bus_set_status, name='api-admin-buses-status'),

    # Car discovery + admin CRUD
    path('cars/', views.car_list, name='api-cars-list'),
    path('cars/<int:pk>/', views.car_detail, name='api-cars-detail'),
    path('admin/cars/', views.admin_car_list_create, name='api-admin-cars-list-create'),
    path('admin/cars/<int:pk>/', views.admin_car_detail, name='api-admin-cars-detail'),
    path('admin/cars/<int:pk>/status/<str:new_status>/', views.admin_car_set_status, name='api-admin-cars-status'),

    # Bus bookings
    path('bus-bookings/', views.bus_booking_list_create, name='api-bus-bookings-list-create'),
    path('bus-bookings/<int:pk>/', views.bus_booking_detail, name='api-bus-bookings-detail'),
    path('bus-bookings/<int:pk>/cancel/', views.bus_booking_cancel, name='api-bus-bookings-cancel'),
    path('bus-bookings/<int:pk>/status/<str:new_status>/', views.bus_booking_set_status, name='api-bus-bookings-status'),

    # Car bookings
    path('car-bookings/', views.car_booking_list_create, name='api-car-bookings-list-create'),
    path('car-bookings/<int:pk>/', views.car_booking_detail, name='api-car-bookings-detail'),
    path('car-bookings/<int:pk>/cancel/', views.car_booking_cancel, name='api-car-bookings-cancel'),
    path('car-bookings/<int:pk>/status/<str:new_status>/', views.car_booking_set_status, name='api-car-bookings-status'),
]
