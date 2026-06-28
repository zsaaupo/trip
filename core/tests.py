from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase
from rest_framework import serializers

from accounts.serializers import ProfileSerializer, RegisterSerializer
from core.validators import MAX_IMAGE_UPLOAD_SIZE, validate_image_upload_size
from hotels.serializers import RoomSerializer
from packages.serializers import PackageSerializer
from transportation.serializers import BusSerializer, CarSerializer


class ImageUploadSizeValidatorTests(SimpleTestCase):
    def test_rejects_image_larger_than_one_mb(self):
        upload = SimpleUploadedFile('photo.jpg', b'x' * (MAX_IMAGE_UPLOAD_SIZE + 1))

        with self.assertRaises(serializers.ValidationError):
            validate_image_upload_size(upload)

    def test_all_photo_serializers_use_size_validator(self):
        serializers_to_check = [
            RegisterSerializer(),
            ProfileSerializer(),
            RoomSerializer(),
            BusSerializer(),
            CarSerializer(),
            PackageSerializer(),
        ]

        for serializer in serializers_to_check:
            with self.subTest(serializer=serializer.__class__.__name__):
                self.assertIn(validate_image_upload_size, serializer.fields['photo'].validators)
