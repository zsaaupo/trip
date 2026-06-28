def get_booking_model(booking_type):
    """Lazy import to avoid circular imports between reviews and the booking apps."""
    from hotels.models import HotelBooking
    from transportation.models import BusBooking, CarBooking
    from packages.models import PackageBooking

    mapping = {
        'hotel': (HotelBooking, lambda b: b.room.hotel),
        'bus': (BusBooking, lambda b: b.bus),
        'car': (CarBooking, lambda b: b.car),
        'package': (PackageBooking, lambda b: b.package),
    }
    return mapping.get(booking_type)
