from django.contrib import admin
from .models import Bus, Car, BusBooking, CarBooking

@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ['name', 'route_origin', 'route_destination', 'trip_date', 'status']
    list_filter = ['status', 'climate_control']

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ['name', 'trip_type', 'capacity', 'status']
    list_filter = ['status', 'trip_type']

@admin.register(BusBooking)
class BusBookingAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'customer', 'bus', 'status', 'total_amount']
    list_filter = ['status']

@admin.register(CarBooking)
class CarBookingAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'customer', 'car', 'status', 'total_amount']
    list_filter = ['status']
