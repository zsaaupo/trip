from rest_framework import serializers
from django.contrib.auth.models import User

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    assigned_user_emails = serializers.SlugRelatedField(
        source='assigned_users', many=True, read_only=True, slug_field='email'
    )

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'expiry_date',
            'min_order_amount', 'max_usage_count', 'used_count', 'is_global',
            'assigned_users', 'assigned_user_emails', 'created_at',
        ]
        read_only_fields = ['used_count', 'created_at']
        extra_kwargs = {'assigned_users': {'write_only': True, 'required': False}}

    def validate_code(self, value):
        return value.upper().strip()


class CouponValidateSerializer(serializers.Serializer):
    code = serializers.CharField()
    order_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
