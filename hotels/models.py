from django.conf import settings
from django.db import models

from core.constants import ApprovalStatus, ClimateControl
from core.models import BookingBase


class Amenity(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.name


class Hotel(models.Model):
    """REQ-HBK-01 / REQ-HBK-04."""
    name = models.CharField(max_length=150)
    location = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.location})"


def room_photo_path(instance, filename):
    return f"rooms/hotel_{instance.hotel_id}/{filename}"


class Room(models.Model):
    """Room attributes table, SRS section 3.2.2."""
    BED_SINGLE = 'single'
    BED_DOUBLE = 'double'
    BED_TYPE_CHOICES = [
        (BED_SINGLE, 'Single (max 2 guests)'),
        (BED_DOUBLE, 'Double (max 4 guests)'),
    ]
    MAX_GUESTS = {BED_SINGLE: 2, BED_DOUBLE: 4}

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name='rooms')
    check_in_date = models.DateField(help_text="Start of the date range this room offer is available for")
    check_out_date = models.DateField(help_text="End of the date range this room offer is available for")
    photo = models.ImageField(upload_to=room_photo_path)
    bed_type = models.CharField(max_length=10, choices=BED_TYPE_CHOICES)
    climate_control = models.CharField(max_length=10, choices=ClimateControl.CHOICES)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name='rooms')
    total_availability = models.PositiveIntegerField(default=1)
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['hotel', 'check_in_date']

    def __str__(self):
        return f"{self.hotel.name} - {self.get_bed_type_display()}"

    @property
    def max_guests(self):
        return self.MAX_GUESTS.get(self.bed_type, 2)

    def available_units(self, check_in, check_out, exclude_booking_id=None):
        """How many identical rooms of this type are free for the requested date range."""
        from core.constants import BookingStatus
        overlapping = HotelBooking.objects.filter(
            room=self,
            status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED],
            check_in_date__lt=check_out,
            check_out_date__gt=check_in,
        )
        if exclude_booking_id:
            overlapping = overlapping.exclude(id=exclude_booking_id)
        booked = overlapping.count()
        return max(self.total_availability - booked, 0)


class HotelBooking(BookingBase):
    """REQ-HBK-08 .. REQ-HBK-15."""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateField()
    check_out_date = models.DateField()
    guests = models.PositiveIntegerField(default=1)

    def __str__(self):
        return self.invoice_id

    @property
    def hotel(self):
        return self.room.hotel
