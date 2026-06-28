from django.contrib import admin
from .models import Package, PackageBooking

@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'type', 'price', 'status']
    list_filter = ['status', 'type']

@admin.register(PackageBooking)
class PackageBookingAdmin(admin.ModelAdmin):
    list_display = ['invoice_id', 'customer', 'package', 'status', 'total_amount']
    list_filter = ['status']
