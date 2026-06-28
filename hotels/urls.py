from django.urls import path
from . import views

urlpatterns = [
    # Customer-facing discovery
    path('', views.hotel_list, name='api-hotels-list'),
    path('amenities/', views.amenity_list, name='api-amenities-list'),
    path('<int:pk>/', views.hotel_detail, name='api-hotels-detail'),

    # Admin CRUD + approvals
    path('admin/', views.admin_hotel_list_create, name='api-admin-hotels-list-create'),
    path('admin/<int:pk>/', views.admin_hotel_detail, name='api-admin-hotels-detail'),
    path('admin/<int:pk>/status/<str:new_status>/', views.admin_hotel_set_status, name='api-admin-hotels-status'),
    path('admin/<int:hotel_id>/rooms/', views.admin_room_list_create, name='api-admin-rooms-list-create'),
    path('admin/rooms/<int:pk>/', views.admin_room_detail, name='api-admin-rooms-detail'),

    # Bookings
    path('bookings/', views.booking_list_create, name='api-hotel-bookings-list-create'),
    path('bookings/<int:pk>/', views.booking_detail, name='api-hotel-bookings-detail'),
    path('bookings/<int:pk>/cancel/', views.booking_cancel, name='api-hotel-bookings-cancel'),
    path('bookings/<int:pk>/status/<str:new_status>/', views.booking_set_status, name='api-hotel-bookings-status'),
]
