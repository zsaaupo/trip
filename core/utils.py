"""
Cross-cutting helper functions (SRS section 3.6):
  - invoice ID generation (3.6.4)
  - cancellation refund calculation (3.6.2)
  - booking status notification emails (3.6.3)
"""
import os
import re
from threading import Thread

# from dotenv import load_dotenv
#
# load_dotenv()
from django.core.mail import EmailMultiAlternatives


from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from core.email_service import send_email


def make_invoice_id(prefix, user):
    """
    <PREFIX>-<USR3>-<YYYYMMDDHHMMSS>  e.g. HBK-JOH-20260615143022
    USR3 = first 3 letters of the customer's name (falls back to username),
    uppercased and padded with 'X' if shorter than 3 characters.
    """
    profile = getattr(user, 'profile', None)
    source = (profile.full_name if profile and profile.full_name else user.username) or 'usr'
    letters = re.sub(r'[^A-Za-z]', '', source)
    usr3 = (letters[:3] or 'USR').upper().ljust(3, 'X')
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    return f"{prefix}-{usr3}-{stamp}"


def calculate_refund_percentage(service_datetime, cancelled_at=None):
    """
    Returns the refund percentage that applies given how many hours remain
    between the cancellation moment and the service date (SRS 3.6.2 / Appendix B).
    """
    cancelled_at = cancelled_at or timezone.now()
    hours_remaining = (service_datetime - cancelled_at).total_seconds() / 3600.0
    for min_hours, refund_pct in settings.CANCELLATION_POLICY:
        if hours_remaining >= min_hours:
            return refund_pct
    return 0


# def send_booking_email(booking, subject, template_lines):
#     """
#     Lightweight notification helper. Uses Django's email backend, which is
#     set to the console backend by default (prints to the terminal) so the
#     project runs with zero extra configuration. Swap EMAIL_BACKEND in
#     settings.py to send real email.
#     """
#     customer = booking.customer
#     body = "\n".join(template_lines)
#     try:
#         send_mail(
#             subject=subject,
#             message=body,
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[customer.email],
#             fail_silently=True,
#         )
#     except Exception:
#         # Notifications must never break the booking flow itself.
#         pass


# def send_email(to, subject, body):
#     html = f"""
#     <html>
#         <body>
#             {body.replace(chr(10), '<br>')}
#         </body>
#     </html>
#     """
#
#     message = EmailMultiAlternatives(
#         subject=subject,
#         body=body,
#         from_email=settings.DEFAULT_FROM_EMAIL,
#         to=[to],
#     )
#
#     message.attach_alternative(html, "text/html")
#     message.send(fail_silently=False)
#
#     print("Email sent successfully")


# def thread_send_email(to, subject, body):
#
#     thread = Thread(target=send_mail, args=(to, subject, body))
#     thread.start()

def notify_status_change(booking, invoice_id, service_label):
    """Sends the appropriate email for the booking's current status (3.6.3)."""
    status_subjects = {
        'pending': f"We received your {service_label} booking ({invoice_id})",
        'confirmed': f"Your {service_label} booking is confirmed ({invoice_id})",
        'declined': f"Your {service_label} booking was declined ({invoice_id})",
        'cancelled': f"Your {service_label} booking was cancelled ({invoice_id})",
        'completed': f"Thanks for travelling with us ({invoice_id})",
    }
    subject = status_subjects.get(booking.status, f"Booking update ({invoice_id})")
    lines = [
        f"Hi {booking.customer.profile.full_name if hasattr(booking.customer, 'profile') else booking.customer.username},",
        "",
        f"Invoice: {invoice_id},",
        f"Status: {booking.get_status_display()},",
        f"Total amount: {booking.total_amount},",
    ]
    if booking.status == 'cancelled' and booking.refund_percentage is not None:
        lines.append(f"Refund: {booking.refund_percentage}% of the paid amount.")
    lines += ["", "Thank you for using Make a trip."]
    email = booking.customer.email

    body = " ".join(lines)

    send_email(
        email,
        subject,
        body
    )