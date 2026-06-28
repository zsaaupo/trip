from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Avg

from core.constants import ApprovalStatus


class ReviewManager(models.Manager):
    def average_for(self, **kwargs):
        """Usage: Review.objects.average_for(hotel=some_hotel_instance)."""
        if not kwargs:
            return None
        obj = next(iter(kwargs.values()))
        if obj is None:
            return None
        ct = ContentType.objects.get_for_model(obj)
        result = self.filter(
            service_content_type=ct, service_object_id=obj.id, status=ApprovalStatus.APPROVED
        ).aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result else None

    def count_for(self, **kwargs):
        obj = next(iter(kwargs.values()))
        if obj is None:
            return 0
        ct = ContentType.objects.get_for_model(obj)
        return self.filter(service_content_type=ct, service_object_id=obj.id, status=ApprovalStatus.APPROVED).count()


class Review(models.Model):
    """
    A rating + comment submitted by a customer after a booking is confirmed
    (REQ-HBK-15 / REQ-TBK-15 / REQ-PKG-10). Admin moderates before it counts
    towards the public average (REQ-ADM-06).
    """
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')

    # The service being reviewed (Hotel, Bus, Car or Package)
    service_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    service_object_id = models.PositiveIntegerField()
    service = GenericForeignKey('service_content_type', 'service_object_id')

    # The specific booking this review is tied to (enforces "one review per booking")
    booking_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+')
    booking_object_id = models.PositiveIntegerField()
    booking = GenericForeignKey('booking_content_type', 'booking_object_id')

    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=ApprovalStatus.CHOICES, default=ApprovalStatus.PENDING)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = ReviewManager()

    class Meta:
        ordering = ['-created_at']
        unique_together = ('booking_content_type', 'booking_object_id')

    def __str__(self):
        return f"{self.rating}* by {self.customer} on {self.service}"
