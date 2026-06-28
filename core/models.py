from django.conf import settings
from django.db import models

from core.constants import BookingStatus, PaymentMethod


class BookingBase(models.Model):
    """
    Common fields for HotelBooking, BusBooking, CarBooking and PackageBooking.
    Each concrete model adds its own FK to the service being booked.
    """
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='%(class)ss')
    invoice_id = models.CharField(max_length=40, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=BookingStatus.CHOICES, default=BookingStatus.PENDING)
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.CHOICES)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Coupon applied at checkout, if any (3.6.7)
    coupon_code = models.CharField(max_length=30, blank=True)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # The date the service actually takes place - used by the cancellation policy
    service_date = models.DateTimeField(help_text="Date/time the booked service takes place (UTC)")

    # T&C acknowledgement (3.2.4 / 3.3.6 / 3.4.4)
    terms_accepted = models.BooleanField(default=False)

    cancelled_at = models.DateTimeField(null=True, blank=True)
    refund_percentage = models.PositiveSmallIntegerField(null=True, blank=True)

    decline_reason = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_id
