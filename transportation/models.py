from django.core.exceptions import ValidationError
from django.db import models
from core.constants import ApprovalStatus, ClimateControl, BookingStatus
from core.models import BookingBase


def bus_photo_path(instance, filename):
    return f"buses/{filename}"


def car_photo_path(instance, filename):
    return f"cars/{filename}"


class Bus(models.Model):
    """Bus attributes table, SRS section 3.3.2."""
    name = models.CharField(max_length=100)
    trip_date = models.DateTimeField()
    photo = models.ImageField(upload_to=bus_photo_path)
    climate_control = models.CharField(max_length=10, choices=ClimateControl.CHOICES)
    route_origin = models.CharField(max_length=100)
    route_destination = models.CharField(max_length=100)
    total_seats = models.PositiveIntegerField()
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['trip_date']

    def __str__(self):
        return f"{self.name}: {self.route_origin} -> {self.route_destination}"

    def occupied_seats(self):
        """Seats currently held by pending/confirmed bookings (REQ-CCR-02 / REQ-TBK-07)."""
        occupied = set()
        active = self.bookings.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED])
        for booking in active:
            occupied.update(booking.seat_list)
        return sorted(occupied)

    def available_seats(self):
        all_seats = set(range(1, self.total_seats + 1))
        return sorted(all_seats - set(self.occupied_seats()))


class Car(models.Model):
    """Car attributes table, SRS section 3.3.4."""
    CAPACITY_CHOICES = [(4, '4 Seats'), (12, '12 Seats'), (28, '28 Seats')]
    TRIP_HOURLY = 'hourly'
    TRIP_ONE_WAY = 'intercity_one_way'
    TRIP_ROUND_TRIP = 'intercity_round_trip'
    TRIP_TYPE_CHOICES = [
        (TRIP_HOURLY, 'Hourly'),
        (TRIP_ONE_WAY, 'Intercity One-Way'),
        (TRIP_ROUND_TRIP, 'Intercity Round Trip'),
    ]

    name = models.CharField(max_length=100, default='Charter Car')
    # trip_date = models.DateTimeField()
    photo = models.ImageField(upload_to=car_photo_path)
    climate_control = models.CharField(max_length=10, choices=ClimateControl.CHOICES)
    capacity = models.PositiveIntegerField(choices=CAPACITY_CHOICES)
    # return_date = models.DateTimeField(null=True, blank=True, help_text="Required for round trips only")
    trip_type = models.CharField(max_length=25, choices=TRIP_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Calculated by admin from trip type and duration")
    status = models.CharField(max_length=10, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['trip_type']

    def __str__(self):
        return f"{self.name} ({self.get_trip_type_display()})"

    # def clean(self):
    #     if self.trip_type == self.TRIP_ROUND_TRIP and not self.return_date:
    #         raise ValidationError("Return date is required for round trips.")
    #
    # def is_booked(self):
    #     return self.bookings.filter(status__in=[BookingStatus.PENDING, BookingStatus.CONFIRMED]).exists()


class BusBooking(BookingBase):
    """REQ-TBK-08, REQ-TBK-10, REQ-TBK-11."""
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='bookings')
    seat_numbers = models.CharField(max_length=255, help_text="Comma-separated seat numbers, e.g. 12,13,14")

    @property
    def seat_list(self):
        return [int(s) for s in self.seat_numbers.split(',') if s.strip().isdigit()]

    def __str__(self):
        return self.invoice_id


class CarBooking(BookingBase):
    """REQ-TBK-08, REQ-TBK-09, REQ-TBK-12."""
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='bookings')
    trip_date = models.DateTimeField()

    def __str__(self):
        return self.invoice_id
