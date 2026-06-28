from django.contrib import admin
from .models import Amenity, Hotel, Room, HotelBooking

admin.site.register(Amenity)

@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['name', 'location']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['hotel', 'bed_type', 'climate_control', 'price_per_night', 'total_availability']
    list_filter = ['bed_type', 'climate_control']

@admin.register(HotelBooking)
class HotelBookingAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'customer', 'room', 'status', 'total_amount', 'created_at']
    list_filter = ['status']
    search_fields = ['invoice_id', 'customer__email']
