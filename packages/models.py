from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from core.constants import ApprovalStatus
from core.models import BookingBase
from hotels.models import Hotel


def package_photo_path(instance, filename):
    return f"packages/{filename}"


class Package(models.Model):
    """Package attributes table, SRS section 3.4.2."""
    TYPE_COUPLE = 'couple'
    TYPE_GROUP = 'group'
    TYPE_SINGLE = 'single'
    TYPE_CHOICES = [
        (TYPE_COUPLE, 'Couple'),
        (TYPE_GROUP, 'Group'),
        (TYPE_SINGLE, 'Single'),
    ]

    name = models.CharField(max_length=150)
    # date = models.DateField(help_text="Package departure/start date")
    location = models.CharField(max_length=150)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    duration = models.CharField(max_length=50, help_text="e.g. 3 Days 2 Nights")

    hotel = models.ForeignKey(Hotel, on_delete=models.SET_NULL, null=True, blank=True, related_name='packages')

    # Transport included may be a Bus or a Car (generic reference)
    transport_content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True, related_name='+'
    )
    transport_object_id = models.PositiveIntegerField(null=True, blank=True)
    transport = GenericForeignKey('transport_content_type', 'transport_object_id')

    inclusions = models.TextField(blank=True, help_text="What is covered")
    exclusions = models.TextField(blank=True, help_text="What is not covered")
    photo = models.ImageField(upload_to=package_photo_path)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Per person")
    status = models.CharField(max_length=10, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.name} ({self.location})"


class PackageBooking(BookingBase):
    """REQ-PKG-05 .. REQ-PKG-10."""
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='bookings')
    num_people = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.invoice_id
