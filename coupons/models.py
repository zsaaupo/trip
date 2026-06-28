from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.constants import DiscountType


class Coupon(models.Model):
    """REQ-CPN-01 .. REQ-CPN-04. Coupon functionality is optional (2.6)."""
    code = models.CharField(max_length=30, unique=True)
    discount_type = models.CharField(max_length=12, choices=DiscountType.CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField()
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_usage_count = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    is_global = models.BooleanField(default=False, help_text="Available to every customer")
    assigned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='coupons',
        help_text="Specific customers this coupon was assigned to (REQ-ADM-05)"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.code

    def eligibility_error(self, user, order_amount):
        """Returns None if usable, otherwise a human-readable reason."""
        if self.expiry_date < timezone.now().date():
            return "This coupon has expired."
        if self.used_count >= self.max_usage_count:
            return "This coupon has reached its usage limit."
        if not self.is_global and not self.assigned_users.filter(id=user.id).exists():
            return "This coupon isn't available on your account."
        if order_amount < self.min_order_amount:
            return f"This coupon requires a minimum order of {self.min_order_amount}."
        return None

    def calculate_discount(self, amount):
        amount = Decimal(amount)
        if self.discount_type == DiscountType.PERCENTAGE:
            discount = amount * (self.discount_value / Decimal('100'))
        else:
            discount = self.discount_value
        return min(discount, amount)
