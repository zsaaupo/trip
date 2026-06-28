from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.constants import ApprovalStatus, BookingStatus
from core.permissions import IsAdminUser
from hotels.models import Hotel, HotelBooking
from transportation.models import Bus, Car, BusBooking, CarBooking
from packages.models import Package, PackageBooking
from reviews.models import Review
from django.contrib.auth.models import User


def _serialize_booking(booking, booking_type, service_name):
    return {
        'id': booking.id,
        'booking_type': booking_type,
        'invoice_id': booking.invoice_id,
        'service_name': service_name,
        'booking_date': booking.created_at,
        'service_date': booking.service_date,
        'status': booking.status,
        'status_display': booking.get_status_display(),
        'total_amount': str(booking.total_amount),
        'payment_method': booking.payment_method,
        'refund_percentage': booking.refund_percentage,
        'customer_email': booking.customer.email,
        'customer_name': getattr(booking.customer.profile, 'full_name', booking.customer.username),
    }


def _gather_all_bookings(status_filter=None, customer=None):
    hotel_qs = HotelBooking.objects.select_related('room__hotel', 'customer__profile').all()
    bus_qs = BusBooking.objects.select_related('bus', 'customer__profile').all()
    car_qs = CarBooking.objects.select_related('car', 'customer__profile').all()
    pkg_qs = PackageBooking.objects.select_related('package', 'customer__profile').all()

    if customer is not None:
        hotel_qs = hotel_qs.filter(customer=customer)
        bus_qs = bus_qs.filter(customer=customer)
        car_qs = car_qs.filter(customer=customer)
        pkg_qs = pkg_qs.filter(customer=customer)

    if status_filter:
        hotel_qs = hotel_qs.filter(status=status_filter)
        bus_qs = bus_qs.filter(status=status_filter)
        car_qs = car_qs.filter(status=status_filter)
        pkg_qs = pkg_qs.filter(status=status_filter)

    rows = []
    rows += [_serialize_booking(b, 'hotel', b.room.hotel.name) for b in hotel_qs]
    rows += [_serialize_booking(b, 'bus', b.bus.name) for b in bus_qs]
    rows += [_serialize_booking(b, 'car', b.car.name) for b in car_qs]
    rows += [_serialize_booking(b, 'package', b.package.name) for b in pkg_qs]
    rows.sort(key=lambda r: r['booking_date'], reverse=True)
    return rows


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_booking_history(request):
    """REQ-UAM-09 / REQ-BHX-01 / REQ-BHX-02: a customer's full cross-module history."""
    status_filter = request.query_params.get('status')
    rows = _gather_all_bookings(status_filter=status_filter, customer=request.user)
    return Response(rows)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_all_bookings(request):
    """Admin: view all bookings across the system (flowchart: 'View All Bookings & Status')."""
    status_filter = request.query_params.get('status')
    rows = _gather_all_bookings(status_filter=status_filter)
    return Response(rows)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def admin_stats(request):
    """REQ-ADM-02: aggregate statistics for the admin dashboard."""
    data = {
        'bookings_per_module': {
            'hotel': HotelBooking.objects.count(),
            'bus': BusBooking.objects.count(),
            'car': CarBooking.objects.count(),
            'package': PackageBooking.objects.count(),
        },
        'pending_booking_approvals': {
            'hotel': HotelBooking.objects.filter(status=BookingStatus.PENDING).count(),
            'bus': BusBooking.objects.filter(status=BookingStatus.PENDING).count(),
            'car': CarBooking.objects.filter(status=BookingStatus.PENDING).count(),
            'package': PackageBooking.objects.filter(status=BookingStatus.PENDING).count(),
        },
        'pending_listing_approvals': {
            'hotel': Hotel.objects.filter(status=ApprovalStatus.PENDING).count(),
            'bus': Bus.objects.filter(status=ApprovalStatus.PENDING).count(),
            'car': Car.objects.filter(status=ApprovalStatus.PENDING).count(),
            'package': Package.objects.filter(status=ApprovalStatus.PENDING).count(),
        },
        'pending_reviews': Review.objects.filter(status=ApprovalStatus.PENDING).count(),
        'total_customers': User.objects.filter(is_staff=False).count(),
        'total_listings': {
            'hotel': Hotel.objects.count(),
            'bus': Bus.objects.count(),
            'car': Car.objects.count(),
            'package': Package.objects.count(),
        },
    }
    # Simple, explicit revenue sum (kept separate from the dict above for clarity)
    from decimal import Decimal
    revenue = Decimal('0')
    for qs in (
        HotelBooking.objects.filter(status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        BusBooking.objects.filter(status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        CarBooking.objects.filter(status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        PackageBooking.objects.filter(status__in=[BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
    ):
        for amount in qs.values_list('total_amount', flat=True):
            revenue += amount
    data['confirmed_revenue'] = str(revenue)
    return Response(data)
