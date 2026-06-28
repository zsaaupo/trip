from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.permissions import IsAdminUser
from .models import Coupon
from .serializers import CouponSerializer, CouponValidateSerializer


@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def coupon_list_create(request):
    if request.method == 'GET':
        return Response(CouponSerializer(Coupon.objects.all(), many=True).data)
    serializer = CouponSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    coupon = serializer.save()
    return Response(CouponSerializer(coupon).data, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAdminUser])
def coupon_detail(request, pk):
    try:
        coupon = Coupon.objects.get(pk=pk)
    except Coupon.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    if request.method == 'GET':
        return Response(CouponSerializer(coupon).data)
    if request.method == 'DELETE':
        coupon.delete()
        return Response(status=204)

    serializer = CouponSerializer(coupon, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_coupons(request):
    """Coupons the logged-in customer can currently use (global or assigned to them)."""
    from django.db.models import Q
    qs = Coupon.objects.filter(
        Q(is_global=True) | Q(assigned_users=request.user),
        expiry_date__gte=timezone.now().date(),
    ).distinct()
    qs = [c for c in qs if c.used_count < c.max_usage_count]
    return Response(CouponSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_coupon(request):
    """REQ-CPN-04: validate eligibility (expiry, minimum order, usage count, user eligibility)."""
    serializer = CouponValidateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    code = serializer.validated_data['code'].upper().strip()
    amount = serializer.validated_data['order_amount']

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return Response({'detail': 'Invalid coupon code.'}, status=400)

    error = coupon.eligibility_error(request.user, amount)
    if error:
        return Response({'detail': error}, status=400)

    discount = coupon.calculate_discount(amount)
    return Response({
        'code': coupon.code,
        'discount_amount': str(discount),
        'final_amount': str(amount - discount),
    })
