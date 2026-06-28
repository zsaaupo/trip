from rest_framework import serializers


MAX_IMAGE_UPLOAD_SIZE = 1 * 1024 * 1024
MAX_IMAGE_UPLOAD_SIZE_MB = MAX_IMAGE_UPLOAD_SIZE // (1024 * 1024)


def validate_image_upload_size(file):
    if file and file.size > MAX_IMAGE_UPLOAD_SIZE:
        raise serializers.ValidationError(
            f"Image size must not be more than {MAX_IMAGE_UPLOAD_SIZE_MB} MB."
        )
    return file
