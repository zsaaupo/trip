from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from core.validators import validate_image_upload_size
from .models import Profile


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    gender = serializers.ChoiceField(choices=Profile.GENDER_CHOICES)
    photo = serializers.ImageField(required=False, allow_null=True, validators=[validate_image_upload_size])
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True, validators=[validate_password])

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def create(self, validated_data):
        email = validated_data['email']
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password'],
            is_active=False,  # REQ-UAM-03: inactive until email verified
        )
        Profile.objects.create(
            user=user,
            full_name=validated_data['full_name'],
            gender=validated_data['gender'],
            photo=validated_data.get('photo'),
            phone=validated_data['phone'],
        )
        return user


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    is_admin = serializers.BooleanField(source='user.is_staff', read_only=True)
    photo = serializers.ImageField(required=False, allow_null=True, validators=[validate_image_upload_size])

    class Meta:
        model = Profile
        fields = ['full_name', 'gender', 'photo', 'phone', 'email', 'is_admin', 'is_email_verified']
        read_only_fields = ['is_email_verified']


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
