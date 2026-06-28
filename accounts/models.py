import random
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def profile_photo_path(instance, filename):
    return f"profile_photos/user_{instance.user_id}/{filename}"


class Profile(models.Model):
    """
    Extends Django's built-in User model with the attributes required by
    REQ-UAM-01 / REQ-UAM-04 (name, gender, photo, phone) plus OTP/email
    verification state (REQ-UAM-02 / REQ-UAM-03).
    Administrator = user.is_staff (no public registration flow per 2.3.2).
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    photo = models.ImageField(upload_to=profile_photo_path, blank=True, null=True)
    phone = models.CharField(max_length=20)

    is_email_verified = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name or self.user.username

    def generate_otp(self):
        self.otp_code = f"{random.randint(0, 999999):06d}"
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp_code', 'otp_created_at'])
        return self.otp_code

    def otp_is_valid(self, code):
        if not self.otp_code or not self.otp_created_at:
            return False
        expiry = self.otp_created_at + timedelta(minutes=settings.OTP_VALIDITY_MINUTES)
        return code == self.otp_code and timezone.now() <= expiry
