from rest_framework import serializers

from core.constants import ApprovalStatus, BookingStatus
from .models import Review
from .utils import get_booking_model


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.profile.full_name', read_only=True)
    service_name = serializers.SerializerMethodField()
    booking_type = serializers.SerializerMethodField()
    invoice_id = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'comment', 'status', 'created_at',
            'customer_name', 'service_name', 'booking_type', 'invoice_id',
        ]
        read_only_fields = ['status', 'created_at']

    def get_service_name(self, obj):
        return str(obj.service) if obj.service else 'Removed listing'

    def get_booking_type(self, obj):
        if not obj.booking_content_type_id:
            return None
        raw = obj.booking_content_type.model  # e.g. 'hotelbooking', 'busbooking'
        return raw.replace('booking', '') if raw.endswith('booking') else raw

    def get_invoice_id(self, obj):
        return getattr(obj.booking, 'invoice_id', None)


class ReviewCreateSerializer(serializers.Serializer):
    booking_type = serializers.ChoiceField(choices=['hotel', 'bus', 'car', 'package'])
    booking_id = serializers.IntegerField()
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        request = self.context['request']
        mapping = get_booking_model(attrs['booking_type'])
        if not mapping:
            raise serializers.ValidationError("Unknown booking type.")
        BookingModel, get_service = mapping
        try:
            booking = BookingModel.objects.get(id=attrs['booking_id'], customer=request.user)
        except BookingModel.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")

        if booking.status not in (BookingStatus.CONFIRMED, BookingStatus.COMPLETED):
            raise serializers.ValidationError("You can only review a booking once it has been confirmed.")

        from django.contrib.contenttypes.models import ContentType
        booking_ct = ContentType.objects.get_for_model(BookingModel)
        if Review.objects.filter(booking_content_type=booking_ct, booking_object_id=booking.id).exists():
            raise serializers.ValidationError("You have already reviewed this booking.")

        attrs['_booking'] = booking
        attrs['_service'] = get_service(booking)
        attrs['_booking_ct'] = booking_ct
        return attrs

    def create(self, validated_data):
        from django.contrib.contenttypes.models import ContentType
        service = validated_data['_service']
        service_ct = ContentType.objects.get_for_model(service)
        return Review.objects.create(
            customer=self.context['request'].user,
            service_content_type=service_ct,
            service_object_id=service.id,
            booking_content_type=validated_data['_booking_ct'],
            booking_object_id=validated_data['_booking'].id,
            rating=validated_data['rating'],
            comment=validated_data.get('comment', ''),
            status=ApprovalStatus.PENDING,
        )
