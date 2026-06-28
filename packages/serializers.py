from rest_framework import serializers

from core.validators import validate_image_upload_size
from reviews.models import Review
from hotels.serializers import HotelAdminSerializer
from .models import Package, PackageBooking


class PackageSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(validators=[validate_image_upload_size])
    hotel_detail = HotelAdminSerializer(source='hotel', read_only=True)
    transport_label = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = Package
        fields = [
            'id', 'name', 'location', 'type', 'duration', 'hotel', 'hotel_detail',
            'transport_content_type', 'transport_object_id', 'transport_label',
            'inclusions', 'exclusions', 'photo', 'price', 'status', 'avg_rating', 'created_at',
        ]

    def get_transport_label(self, obj):
        return str(obj.transport) if obj.transport else None

    def get_avg_rating(self, obj):
        return Review.objects.average_for(package=obj)


class PackageBookingSerializer(serializers.ModelSerializer):
    package_detail = PackageSerializer(source='package', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PackageBooking
        fields = [
            'id', 'invoice_id', 'package', 'package_detail', 'num_people', 'status',
            'status_display', 'payment_method', 'total_amount', 'coupon_code',
            'discount_amount', 'service_date', 'terms_accepted', 'cancelled_at',
            'refund_percentage', 'decline_reason', 'created_at', 'service_date',
        ]
        read_only_fields = [
            'invoice_id', 'status', 'total_amount', 'discount_amount',
            'cancelled_at', 'refund_percentage', 'decline_reason', 'created_at',
        ]

    def validate(self, attrs):
        if attrs.get('num_people', 1) < 1:
            raise serializers.ValidationError("Number of people must be at least 1.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the Terms & Conditions to confirm a booking.")
        return attrs
