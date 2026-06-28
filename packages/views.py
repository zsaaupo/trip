from datetime import datetime, time, timezone as dt_timezone
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
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
from transportation.models import Bus, Car

from .models import Package, PackageBooking
from .serializers import PackageSerializer, PackageBookingSerializer


def _resolve_transport(transport_type, transport_id):
    if not transport_type or not transport_id:
        return None, None
    model = {'bus': Bus, 'car': Car}.get(transport_type)
    if not model:
        return None, None
    obj = model.objects.filter(id=transport_id).first()
    if not obj:
        return None, None
    return ContentType.objects.get_for_model(model), obj.id


# ---------------------------------------------------------------------------
# Customer discovery (REQ-PKG-03/04)
# ---------------------------------------------------------------------------
@api_view(['GET'])
@permission_classes([AllowAny])
def package_list(request):
    qs = Package.objects.filter(status=ApprovalStatus.APPROVED)
    location = request.query_params.get('location')
    if location:
        qs = qs.filter(location__icontains=location)
    ptype = request.query_params.get('type')
    if ptype:
        qs = qs.filter(type=ptype)

    packages = list(qs)
    sort = request.query_params.get('sort')
    if sort == 'rating':
        packages.sort(key=lambda p: Review.objects.average_for(package=p) or 0, reverse=True)
    elif sort == 'price_low':
        packages.sort(key=lambda p: p.price)
    elif sort == 'price_high':
        packages.sort(key=lambda p: p.price, reverse=True)
    return Response(PackageSerializer(packages, many=True, context={'request': request}).data)


@api_view(['GET'])
@permission_classes([AllowAny])
def package_detail(request, pk):
    package = get_object_or_404(Package, pk=pk, status=ApprovalStatus.APPROVED)
    return Response(PackageSerializer(package, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Admin CRUD + approvals (REQ-PKG-01/02)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_package_list_create(request):
    if request.method == 'GET':
        return Response(PackageSerializer(Package.objects.all(), many=True, context={'request': request}).data)

    data = request.data.copy()
    ct, obj_id = _resolve_transport(data.get('transport_type'), data.get('transport_id'))
    if ct:
        data['transport_content_type'] = ct.id
        data['transport_object_id'] = obj_id
    serializer = PackageSerializer(data=data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    package = serializer.save()
    return Response(PackageSerializer(package, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def admin_package_detail(request, pk):
    package = get_object_or_404(Package, pk=pk)
    if request.method == 'GET':
        return Response(PackageSerializer(package, context={'request': request}).data)
    if request.method == 'DELETE':
        package.delete()
        return Response(status=204)

    data = request.data.copy()
    ct, obj_id = _resolve_transport(data.get('transport_type'), data.get('transport_id'))
    if ct:
        data['transport_content_type'] = ct.id
        data['transport_object_id'] = obj_id
    serializer = PackageSerializer(package, data=data, partial=True, context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def admin_package_set_status(request, pk, new_status):
    if new_status not in (ApprovalStatus.APPROVED, ApprovalStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    package = get_object_or_404(Package, pk=pk)
    package.status = new_status
    package.save(update_fields=['status'])
    return Response(PackageSerializer(package, context={'request': request}).data)


# ---------------------------------------------------------------------------
# Bookings (REQ-PKG-05 .. REQ-PKG-10)
# ---------------------------------------------------------------------------
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def booking_list_create(request):
    if request.method == 'GET':
        if request.user.is_staff and request.query_params.get('all') == '1':
            qs = PackageBooking.objects.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
        else:
            qs = PackageBooking.objects.filter(customer=request.user)
        return Response(PackageBookingSerializer(qs, many=True, context={'request': request}).data)

    serializer = PackageBookingSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    package = data['package']
    num_people = data.get('num_people', 1)
    subtotal = package.price * num_people

    coupon_code = request.data.get('coupon_code', '').strip().upper()
    discount = Decimal('0')
    if coupon_code:
        try:
            coupon = Coupon.objects.get(code=coupon_code)
        except Coupon.DoesNotExist:
            return Response({'detail': 'Invalid coupon code.'}, status=400)
        error = coupon.eligibility_error(request.user, subtotal)
        if error:
            return Response({'detail': error}, status=400)
        discount = coupon.calculate_discount(subtotal)
        coupon.used_count += 1
        coupon.save(update_fields=['used_count'])

    service_dt = data['service_date']

    booking = PackageBooking.objects.create(
        customer=request.user,
        package=package,
        num_people=num_people,
        invoice_id=make_invoice_id('PBK', request.user),
        status=BookingStatus.PENDING,
        payment_method=data['payment_method'],
        total_amount=subtotal - discount,
        coupon_code=coupon_code,
        discount_amount=discount,
        service_date=service_dt,
        terms_accepted=True,
    )
    notify_status_change(booking, booking.invoice_id, "tour package")
    return Response(PackageBookingSerializer(booking, context={'request': request}).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def booking_detail(request, pk):
    booking = get_object_or_404(PackageBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    return Response(PackageBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def booking_cancel(request, pk):
    booking = get_object_or_404(PackageBooking, pk=pk)
    if booking.customer_id != request.user.id and not request.user.is_staff:
        return Response({'detail': 'Not allowed.'}, status=403)
    if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
        return Response({'detail': 'This booking can no longer be cancelled.'}, status=400)
    now = timezone.now()
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now
    booking.refund_percentage = calculate_refund_percentage(booking.service_date, now)
    booking.save(update_fields=['status', 'cancelled_at', 'refund_percentage'])
    notify_status_change(booking, booking.invoice_id, "tour package")
    return Response(PackageBookingSerializer(booking, context={'request': request}).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def booking_set_status(request, pk, new_status):
    if new_status not in (BookingStatus.CONFIRMED, BookingStatus.DECLINED):
        return Response({'detail': 'Invalid status.'}, status=400)
    booking = get_object_or_404(PackageBooking, pk=pk)
    booking.status = new_status
    if new_status == BookingStatus.DECLINED:
        booking.decline_reason = request.data.get('reason', '')
    booking.save(update_fields=['status', 'decline_reason'])
    notify_status_change(booking, booking.invoice_id, "tour package")
    return Response(PackageBookingSerializer(booking, context={'request': request}).data)
