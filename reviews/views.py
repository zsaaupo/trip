from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from core.constants import ApprovalStatus
from core.permissions import IsAdminUser
from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer
from .utils import get_booking_model


@api_view(['GET'])
@permission_classes([AllowAny])
def list_reviews(request):
    """Public: approved reviews for a given service, e.g. ?service_type=hotel&service_id=3"""
    service_type = request.query_params.get('service_type')
    service_id = request.query_params.get('service_id')
    if not service_type or not service_id:
        return Response({'detail': 'service_type and service_id are required.'}, status=400)

    mapping = get_booking_model(service_type)
    if not mapping:
        return Response({'detail': 'Unknown service type.'}, status=400)
    _, get_service = mapping
    BookingModel = mapping[0]
    # Resolve the actual service model from the booking mapping's lambda target class
    service_model = {
        'hotel': __import__('hotels.models', fromlist=['Hotel']).Hotel,
        'bus': __import__('transportation.models', fromlist=['Bus']).Bus,
        'car': __import__('transportation.models', fromlist=['Car']).Car,
        'package': __import__('packages.models', fromlist=['Package']).Package,
    }[service_type]

    try:
        service_obj = service_model.objects.get(id=service_id)
    except service_model.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    ct = ContentType.objects.get_for_model(service_obj)
    qs = Review.objects.filter(
        service_content_type=ct, service_object_id=service_obj.id, status=ApprovalStatus.APPROVED
    )
    return Response(ReviewSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_review(request):
    serializer = ReviewCreateSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)
    review = serializer.save()
    return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def pending_reviews(request):
    qs = Review.objects.filter(status=ApprovalStatus.PENDING)
    return Response(ReviewSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def moderate_review(request, review_id):
    """REQ-ADM-06: approve or decline a customer review before it counts publicly."""
    try:
        review = Review.objects.get(id=review_id)
    except Review.DoesNotExist:
        return Response({'detail': 'Not found.'}, status=404)

    new_status = request.data.get('status')
    if new_status not in (ApprovalStatus.APPROVED, ApprovalStatus.DECLINED):
        return Response({'detail': 'status must be approved or declined.'}, status=400)

    review.status = new_status
    review.save(update_fields=['status'])
    return Response(ReviewSerializer(review).data)
