"""
Shared choice constants used across the Hotel, Transportation and
Tour Package modules (SRS section 3.6).
"""

class BookingStatus:
    PENDING = 'pending'
    CONFIRMED = 'confirmed'
    DECLINED = 'declined'
    CANCELLED = 'cancelled'
    COMPLETED = 'completed'

    CHOICES = [
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (DECLINED, 'Declined'),
        (CANCELLED, 'Cancelled'),
        (COMPLETED, 'Completed'),
    ]


class ApprovalStatus:
    """Used for listings (hotels, buses, cars, packages) before they go live."""
    PENDING = 'pending'
    APPROVED = 'approved'
    DECLINED = 'declined'

    CHOICES = [
        (PENDING, 'Pending'),
        (APPROVED, 'Approved'),
        (DECLINED, 'Declined'),
    ]


class PaymentMethod:
    CASH_ON_ARRIVAL = 'cash_on_arrival'
    PAY_NOW = 'pay_now'

    CHOICES = [
        (CASH_ON_ARRIVAL, 'Cash on Arrival'),
        (PAY_NOW, 'Pay Now'),
    ]


class ClimateControl:
    AC = 'ac'
    NON_AC = 'non_ac'

    CHOICES = [
        (AC, 'AC'),
        (NON_AC, 'Non-AC'),
    ]


class DiscountType:
    FIXED = 'fixed'
    PERCENTAGE = 'percentage'

    CHOICES = [
        (FIXED, 'Fixed Amount'),
        (PERCENTAGE, 'Percentage'),
    ]
