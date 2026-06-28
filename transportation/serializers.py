from rest_framework import serializers

from core.validators import validate_image_upload_size
from reviews.models import Review
from .models import Bus, Car, BusBooking, CarBooking


class BusSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(validators=[validate_image_upload_size])
    avg_rating = serializers.SerializerMethodField()
    available_seats = serializers.SerializerMethodField()
    occupied_seats = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'name', 'trip_date', 'photo', 'climate_control', 'route_origin',
            'route_destination', 'total_seats', 'price_per_seat', 'status',
            'avg_rating', 'available_seats', 'occupied_seats', 'created_at',
        ]

    def get_avg_rating(self, obj):
        return Review.objects.average_for(bus=obj)

    def get_available_seats(self, obj):
        return obj.available_seats()

    def get_occupied_seats(self, obj):
        return obj.occupied_seats()


class CarSerializer(serializers.ModelSerializer):
    photo = serializers.ImageField(validators=[validate_image_upload_size])
    avg_rating = serializers.SerializerMethodField()
    # is_booked = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = [
            'id', 'name', 'photo', 'climate_control', 'capacity',
            'trip_type', 'price', 'status', 'avg_rating', 'created_at',
        ]

    def get_avg_rating(self, obj):
        return Review.objects.average_for(car=obj)

    # def get_is_booked(self, obj):
    #     return obj.is_booked()


class BusBookingSerializer(serializers.ModelSerializer):
    bus_detail = BusSerializer(source='bus', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    seat_list = serializers.ListField(child=serializers.IntegerField(), read_only=True)

    class Meta:
        model = BusBooking
        fields = [
            'id', 'invoice_id', 'bus', 'bus_detail', 'seat_numbers', 'seat_list',
            'status', 'status_display', 'payment_method', 'total_amount',
            'coupon_code', 'discount_amount', 'service_date', 'terms_accepted',
            'cancelled_at', 'refund_percentage', 'decline_reason', 'created_at',
        ]
        read_only_fields = [
            'invoice_id', 'status', 'total_amount', 'discount_amount', 'service_date',
            'cancelled_at', 'refund_percentage', 'decline_reason', 'created_at',
        ]

    def validate(self, attrs):
        bus = attrs['bus']
        requested = [s.strip() for s in attrs['seat_numbers'].split(',') if s.strip()]
        if not requested:
            raise serializers.ValidationError("Select at least one seat.")
        try:
            requested_ints = [int(s) for s in requested]
        except ValueError:
            raise serializers.ValidationError("Seat numbers must be integers.")
        if any(s < 1 or s > bus.total_seats for s in requested_ints):
            raise serializers.ValidationError("One or more seat numbers are out of range for this bus.")
        occupied = set(bus.occupied_seats())
        clashing = occupied.intersection(requested_ints)
        if clashing:
            raise serializers.ValidationError(f"Seat(s) {sorted(clashing)} are already taken.")
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the Terms & Conditions to confirm a booking.")
        attrs['seat_numbers'] = ','.join(str(s) for s in requested_ints)
        return attrs


class CarBookingSerializer(serializers.ModelSerializer):
    car_detail = CarSerializer(source='car', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CarBooking
        fields = [
            'id', 'invoice_id', 'car', 'car_detail', 'status', 'status_display',
            'payment_method', 'total_amount', 'coupon_code', 'discount_amount',
            'service_date', 'terms_accepted', 'cancelled_at', 'refund_percentage',
            'decline_reason', 'created_at', 'trip_date',
        ]
        read_only_fields = [
            'invoice_id', 'status', 'total_amount', 'discount_amount', 'service_date',
            'cancelled_at', 'refund_percentage', 'decline_reason', 'created_at',
        ]

    def validate(self, attrs):
        if not attrs.get('terms_accepted'):
            raise serializers.ValidationError("You must accept the Terms & Conditions to confirm a booking.")
        return attrs
