"""
Transitions CONFIRMED bookings whose service date has passed into
COMPLETED (SRS 3.6.3 booking status lifecycle). Run this periodically,
e.g. via cron or a scheduled task:

    python manage.py mark_completed_bookings
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.constants import BookingStatus
from core.utils import notify_status_change
from hotels.models import HotelBooking
from transportation.models import BusBooking, CarBooking
from packages.models import PackageBooking


class Command(BaseCommand):
    help = "Marks confirmed bookings as completed once their service date has passed."

    def handle(self, *args, **options):
        now = timezone.now()
        total = 0
        for model, label in [
            (HotelBooking, "hotel room"), (BusBooking, "bus"),
            (CarBooking, "car"), (PackageBooking, "tour package"),
        ]:
            qs = model.objects.filter(status=BookingStatus.CONFIRMED, service_date__lt=now)
            for booking in qs:
                booking.status = BookingStatus.COMPLETED
                booking.save(update_fields=['status'])
                notify_status_change(booking, booking.invoice_id, label)
                total += 1
        self.stdout.write(self.style.SUCCESS(f"Marked {total} booking(s) as completed."))
