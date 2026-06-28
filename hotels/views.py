from datetime import datetime, time, timezone as dt_timezone
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
from reviews.models import Review

from .models import Amenity, Hotel, Room, HotelBooking
from .serializers import (
    AmenitySerializer, HotelSerializer, HotelAdminSerializer, RoomSerializer, HotelBookingSerializer,
)


# ---------------------------------------------------------------------------
# Customer-facing discovery (REQ-HBK-05 .. REQ-HBK-07)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def hotel_list(request):
    qs = Hotel.objects.filter(status=ApprovalStatus.APPROVED)

    location = request.query_params.get('location')
    if location:
        qs = qs.filter(location__icontains=location)

    check_in = request.query_params.get('check_in')
    check_out = request.query_params.get('check_out')
    if check_in and check_out:
        qs = qs.filter(rooms__check_in_date__lte=check_in, rooms__check_out_date__gte=check_out).distinct()

    hotels = list(qs)
    sort = request.query_params.get('sort')
    if sort == 'rating':
        hotels.sort(key=lambda h: Review.objects.average_for(hotel=h) or 0, reverse=True)
    elif sort == 'price_low':
        hotels.sort(key=lambda h: min([r.price_per_night for r in h.rooms.all()], default=Decimal('999999')))
    elif sort == 'price_high':
        hotels.sort(key=lambda h: min([r.price_per_night for r in h.rooms.all()], default=Decimal('0')), reverse=True)

    data = HotelSerializer(hotels, many=True, context={'request': request}).data
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk, status=ApprovalStatus.APPROVED)
    return Response(HotelSerializer(hotel, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def amenity_list(request):
    return Response(AmenitySerializer(Amenity.objects.all(), many=True).data)


# ---------------------------------------------------------------------------
# Admin: Hotel & Room CRUD + approvals (REQ-HBK-01 .. REQ-HBK-03)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def admin_hotel_list_create(request):
    if request.method == 'GET':
        return Response(HotelAdminSerializer(Hotel.objects.all(), many=True).data)
    serializer = HotelAdminSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    hotel = serializer.save()
    return Response(HotelAdminSerializer(hotel).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def admin_hotel_detail(request, pk):
    hotel = get_object_or_404(Hotel, pk=pk)
    if request.method == 'GET':
        return Response(HotelAdminSerializer(hotel).data)
    if request.method == 'DELETE':
        hotel.delete()
        return Response(status=204)
    serializer = HotelAdminSerializer(hotel, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_hotel_set_status(request, pk, new_status):
    if new_status not in (ApprovalStatus.APPROVED, ApprovalStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    hotel = get_object_or_404(Hotel, pk=pk)
    hotel.status = new_status
    hotel.save(update_fields=['status'])
    return Response(HotelAdminSerializer(hotel).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_room_list_create(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    if request.method == 'GET':
        return Response(RoomSerializer(hotel.rooms.all(), many=True, context={'request': request}).data)
    data = request.data.copy()
    data['hotel'] = hotel.id
    serializer = RoomSerializer(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    room = serializer.save()
    return Response(RoomSerializer(room, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_room_detail(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == 'GET':
        return Response(RoomSerializer(room, context={'request': request}).data)
    if request.method == 'DELETE':
        room.delete()
        return Response(status=204)
    serializer = RoomSerializer(room, data=request.data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Customer: booking lifecycle (REQ-HBK-08 .. REQ-HBK-14)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def booking_list_create(request):
    if request.method == 'GET':
        if request.user.is_staff and request.query_params.get('all') == '1':
            qs = HotelBooking.objects.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            qs = HotelBooking.objects.filter(customer=request.user)
        return Response(HotelBookingSerializer(qs, many=True, context={'request': request}).data)

    serializer = HotelBookingSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    room = data['room']
    nights = (data['check_out_date'] - data['check_in_date']).days
    subtotal = room.price_per_night * nights

    discount_amount = Decimal('0')
    coupon_code = request.data.get('coupon_code', '').strip().upper()
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code.'}, status=400)
        error = coupon.eligibility_error(request.user, subtotal)
        if error:
            return Response({'detail': error}, status=400)
        discount_amount = coupon.calculate_discount(subtotal)
        coupon.used_count += 1
        coupon.save(update_fields=['used_count'])

    total_amount = subtotal - discount_amount
    # Hotel check-in is treated as the service moment for the cancellation policy (3.6.2)
    naive_checkin = datetime.combine(data['check_in_date'], time(14, 0))
    service_dt = timezone.make_aware(naive_checkin, dt_timezone.utc)

    booking = HotelBooking.objects.create(
        customer=request.user,
        room=room,
        check_in_date=data['check_in_date'],
        check_out_date=data['check_out_date'],
        guests=data.get('guests', 1),
        invoice_id=make_invoice_id('HBK', request.user),
        status=BookingStatus.PENDING,
        payment_method=data['payment_method'],
        total_amount=total_amount,
        coupon_code=coupon_code,
        discount_amount=discount_amount,
        service_date=service_dt,
        terms_accepted=True,
    )
    notify_status_change(booking, booking.invoice_id, "hotel room")
    return Response(HotelBookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    booking = get_object_or_404(HotelBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    return Response(HotelBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, pk):
    booking = get_object_or_404(HotelBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return Response({'detail': 'This booking can no longer be cancelled.'}, status=400)

    now = timezone.now()
    refund_pct = calculate_refund_percentage(booking.service_date, now)
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now
    booking.refund_percentage = refund_pct
    booking.save(update_fields=['status', 'cancelled_at', 'refund_percentage'])
    notify_status_change(booking, booking.invoice_id, "hotel room")
    return Response(HotelBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def booking_set_status(request, pk, new_status):
    """Admin approves/declines a hotel booking (REQ-HBK-03)."""
    if new_status not in (BookingStatus.CONFIRMED, BookingStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    booking = get_object_or_404(HotelBooking, pk=pk)
    booking.status = new_status
    if new_status == BookingStatus.DECLINED:
        booking.decline_reason = request.data.get('reason', '')
    booking.save(update_fields=['status', 'decline_reason'])
    notify_status_change(booking, booking.invoice_id, "hotel room")
    return Response(HotelBookingSerializer(booking, context={'request': request}).data)
