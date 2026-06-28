from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.constants import ApprovalStatus, BookingStatus
from core.permissions import IsAdminUser
from core.utils import make_invoice_id, calculate_refund_percentage, notify_status_change
from coupons.models import Coupon

from .models import Bus, Car, BusBooking, CarBooking
from .serializers import BusSerializer, CarSerializer, BusBookingSerializer, CarBookingSerializer


# ---------------------------------------------------------------------------
# Bus discovery (REQ-TBK-05, REQ-TBK-07) + admin CRUD (REQ-TBK-01/02)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def bus_list(request):
    qs = Bus.objects.filter(status=ApprovalStatus.APPROVED)
    location = request.query_params.get('location')
    if location:
        qs = qs.filter(route_origin__icontains=location) | qs.filter(route_destination__icontains=location)
    trip_date = request.query_params.get('trip_date')
    if trip_date:
        qs = qs.filter(trip_date__date=trip_date)
    buses = list(qs)
    sort = request.query_params.get('sort')
    if sort == 'price_low':
        buses.sort(key=lambda b: b.price_per_seat)
    elif sort == 'price_high':
        buses.sort(key=lambda b: b.price_per_seat, reverse=True)
    return Response(BusSerializer(buses, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def bus_detail(request, pk):
    bus = get_object_or_404(Bus, pk=pk, status=ApprovalStatus.APPROVED)
    return Response(BusSerializer(bus, context={'request': request}).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_bus_list_create(request):
    if request.method == 'GET':
        return Response(BusSerializer(Bus.objects.all(), many=True, context={'request': request}).data)
    serializer = BusSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    bus = serializer.save()
    return Response(BusSerializer(bus, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_bus_detail(request, pk):
    bus = get_object_or_404(Bus, pk=pk)
    if request.method == 'GET':
        return Response(BusSerializer(bus, context={'request': request}).data)
    if request.method == 'DELETE':
        bus.delete()
        return Response(status=204)
    serializer = BusSerializer(bus, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_bus_set_status(request, pk, new_status):
    if new_status not in (ApprovalStatus.APPROVED, ApprovalStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    bus = get_object_or_404(Bus, pk=pk)
    bus.status = new_status
    bus.save(update_fields=['status'])
    return Response(BusSerializer(bus, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Car discovery + admin CRUD (REQ-TBK-03/04/06)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def car_list(request):
    qs = Car.objects.filter(status=ApprovalStatus.APPROVED)
    trip_type = request.query_params.get('trip_type')
    if trip_type:
        qs = qs.filter(trip_type=trip_type)
    capacity = request.query_params.get('capacity')
    if capacity:
        qs = qs.filter(capacity=capacity)
    cars = [c for c in qs]
    return Response(CarSerializer(cars, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk, status=ApprovalStatus.APPROVED)
    return Response(CarSerializer(car, context={'request': request}).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_car_list_create(request):
    if request.method == 'GET':
        return Response(CarSerializer(Car.objects.all(), many=True, context={'request': request}).data)
    serializer = CarSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    car = serializer.save()
    return Response(CarSerializer(car, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_car_detail(request, pk):
    car = get_object_or_404(Car, pk=pk)
    if request.method == 'GET':
        return Response(CarSerializer(car, context={'request': request}).data)
    if request.method == 'DELETE':
        car.delete()
        return Response(status=204)
    serializer = CarSerializer(car, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_car_set_status(request, pk, new_status):
    if new_status not in (ApprovalStatus.APPROVED, ApprovalStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    car = get_object_or_404(Car, pk=pk)
    car.status = new_status
    car.save(update_fields=['status'])
    return Response(CarSerializer(car, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Helper shared by both booking creation endpoints
# ---------------------------------------------------------------------------
def _apply_coupon(request, subtotal):
    """Returns (discount_amount, coupon_code) or raises via Response tuple (None, response)."""
    coupon_code = request.data.get('coupon_code', '').strip().upper()
    if not coupon_code:
        return Decimal('0'), '', None
    try:
        coupon = Coupon.objects.get(code=coupon_code)
    except Coupon.DoesNotExist:
        return None, None, Response({'detail': 'Invalid coupon code.'}, status=400)
    error = coupon.eligibility_error(request.user, subtotal)
    if error:
        return None, None, Response({'detail': error}, status=400)
    discount = coupon.calculate_discount(subtotal)
    coupon.used_count += 1
    coupon.save(update_fields=['used_count'])
    return discount, coupon_code, None


# ---------------------------------------------------------------------------
# Bus bookings (REQ-TBK-08, 10, 11, 13, 14, 15)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def bus_booking_list_create(request):
    if request.method == 'GET':
        if request.user.is_staff and request.query_params.get('all') == '1':
            qs = BusBooking.objects.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            qs = BusBooking.objects.filter(customer=request.user)
        return Response(BusBookingSerializer(qs, many=True, context={'request': request}).data)

    serializer = BusBookingSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    bus = data['bus']
    num_seats = len(data['seat_numbers'].split(','))
    subtotal = bus.price_per_seat * num_seats

    discount, coupon_code, error_response = _apply_coupon(request, subtotal)
    if error_response:
        return error_response

    booking = BusBooking.objects.create(
        customer=request.user,
        bus=bus,
        seat_numbers=data['seat_numbers'],
        invoice_id=make_invoice_id('BBK', request.user),
        status=BookingStatus.PENDING,
        payment_method=data['payment_method'],
        total_amount=subtotal - discount,
        coupon_code=coupon_code,
        discount_amount=discount,
        service_date=bus.trip_date,
        terms_accepted=True,
    )
    notify_status_change(booking, booking.invoice_id, "bus")
    return Response(BusBookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def bus_booking_detail(request, pk):
    booking = get_object_or_404(BusBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    return Response(BusBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bus_booking_cancel(request, pk):
    booking = get_object_or_404(BusBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return Response({'detail': 'This booking can no longer be cancelled.'}, status=400)
    now = timezone.now()
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now
    booking.refund_percentage = calculate_refund_percentage(booking.service_date, now)
    booking.save(update_fields=['status', 'cancelled_at', 'refund_percentage'])
    notify_status_change(booking, booking.invoice_id, "bus")
    return Response(BusBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def bus_booking_set_status(request, pk, new_status):
    if new_status not in (BookingStatus.CONFIRMED, BookingStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    booking = get_object_or_404(BusBooking, pk=pk)
    booking.status = new_status
    if new_status == BookingStatus.DECLINED:
        booking.decline_reason = request.data.get('reason', '')
    booking.save(update_fields=['status', 'decline_reason'])
    notify_status_change(booking, booking.invoice_id, "bus")
    return Response(BusBookingSerializer(booking, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Car bookings (REQ-TBK-08, 09, 12, 13, 14, 15)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def car_booking_list_create(request):
    if request.method == 'GET':
        if request.user.is_staff and request.query_params.get('all') == '1':
            qs = CarBooking.objects.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            qs = CarBooking.objects.filter(customer=request.user)
        return Response(CarBookingSerializer(qs, many=True, context={'request': request}).data)

    serializer = CarBookingSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    print(data)
    car = data['car']
    subtotal = car.price
    discount, coupon_code, error_response = _apply_coupon(request, subtotal)
    if error_response:
        return error_response

    booking = CarBooking.objects.create(
        customer=request.user,
        car=car,
        invoice_id=make_invoice_id('CBK', request.user),
        status=BookingStatus.PENDING,
        payment_method=data['payment_method'],
        total_amount=subtotal - discount,
        coupon_code=coupon_code,
        discount_amount=discount,
        service_date=data['trip_date'],
        trip_date=data['trip_date'],
        terms_accepted=True,
    )
    notify_status_change(booking, booking.invoice_id, "car")
    return Response(CarBookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def car_booking_detail(request, pk):
    booking = get_object_or_404(CarBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    return Response(CarBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def car_booking_cancel(request, pk):
    booking = get_object_or_404(CarBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return Response({'detail': 'This booking can no longer be cancelled.'}, status=400)
    now = timezone.now()
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now
    booking.refund_percentage = calculate_refund_percentage(booking.service_date, now)
    booking.save(update_fields=['status', 'cancelled_at', 'refund_percentage'])
    notify_status_change(booking, booking.invoice_id, "car")
    return Response(CarBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def car_booking_set_status(request, pk, new_status):
    if new_status not in (BookingStatus.CONFIRMED, BookingStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    booking = get_object_or_404(CarBooking, pk=pk)
    booking.status = new_status
    if new_status == BookingStatus.DECLINED:
        booking.decline_reason = request.data.get('reason', '')
    booking.save(update_fields=['status', 'decline_reason'])
    notify_status_change(booking, booking.invoice_id, "car")
    return Response(CarBookingSerializer(booking, context={'request': request}).data)
