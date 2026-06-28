from rest_framework import serializers

from core.validators import validate_image_upload_size
from reviews.models import Review
from .models import Amenity, Hotel, Room, HotelBooking


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ['id', 'name']


class RoomSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(validators=[validate_image_upload_size])
    amenities = AmenitySerializer(many=True, read_only=True)
    amenity_ids = serializers.PrimaryKeyRelatedField(
        queryset=Amenity.objects.all(), many=True, write_only=True, required=False, source='amenities'
    )
    max_guests = serializers.IntegerField(read_only=True)
    available_units = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = [
            'id', 'hotel', 'check_in_date', 'check_out_date', 'photo', 'bed_type',
            'climate_control', 'amenities', 'amenity_ids', 'total_availability',
            'price_per_night', 'max_guests', 'available_units',
        ]

    def get_available_units(self, obj):
        request = self.context.get('request')
        if not request:
            return obj.total_availability
        ci, co = request.query_params.get('check_in'), request.query_params.get('check_out')
        if ci and co:
            return obj.available_units(ci, co)
        return obj.total_availability


class HotelSerializer(serializers.ModelSerializer):
    rooms = RoomSerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()

    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location', 'description', 'status', 'rooms', 'avg_rating', 'min_price', 'created_at']

    def get_avg_rating(self, obj):
        return Review.objects.average_for(hotel=obj)

    def get_min_price(self, obj):
        prices = [r.price_per_night for r in obj.rooms.all()]
        return min(prices) if prices else None


class HotelAdminSerializer(serializers.ModelSerializer):
    """Used by the admin CRUD endpoints - no nested rooms needed there."""
    class Meta:
        model = Hotel
        fields = ['id', 'name', 'location', 'description', 'status', 'created_at']


class HotelBookingSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(source='room.hotel.name', read_only=True)
    hotel_location = serializers.CharField(source='room.hotel.location', read_only=True)
    room_detail = RoomSerializer(source='room', read_only=True)
    customer_name = serializers.CharField(source='customer.profile.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = HotelBooking
        fields = [
            'id', 'invoice_id', 'room', 'room_detail', 'hotel_name', 'hotel_location',
            'check_in_date', 'check_out_date', 'guests', 'status', 'status_display',
            'payment_method', 'total_amount', 'coupon_code', 'discount_amount',
            'service_date', 'terms_accepted', 'cancelled_at', 'refund_percentage',
            'decline_reason', 'customer_name', 'created_at',
        ]
        read_only_fields = [
            'invoice_id', 'status', 'total_amount', 'discount_amount', 'service_date',
            'cancelled_at', 'refund_percentage', 'decline_reason', 'created_at',
        ]

    def validate(self, attrs):
        room = attrs['room']
        check_in = attrs['check_in_date']
        check_out = attrs['check_out_date']
        guests = attrs.get('guests', 1)

        if check_out <= check_in:
            raise serializers.ValidationError("Check-out date must be after check-in date.")
        if check_in < room.check_in_date or check_out > room.check_out_date:
            raise serializers.ValidationError("Selected dates are outside this room's available date range.")
        if guests > room.max_guests:
            raise serializers.ValidationError(f"This room type allows a maximum of {room.max_guests} guests.")
        if room.available_units(check_in, check_out) <= 0:
            raise serializers.ValidationError("No rooms of this type are available for the selected dates.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the Terms & Conditions to confirm a booking.")
        return attrs
