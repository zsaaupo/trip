from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'expiry_date', 'used_count', 'max_usage_count', 'is_global']
    list_filter = ['discount_type', 'is_global']
