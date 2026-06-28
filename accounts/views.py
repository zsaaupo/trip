# from dotenv import load_dotenv
#
# load_dotenv()
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes, throttle_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .models import Profile
from .serializers import (
    RegisterSerializer, VerifyOTPSerializer, ResendOTPSerializer,
    LoginSerializer, ProfileSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
)
from core.email_service import send_email

class LoginRateThrottle(AnonRateThrottle):
    """NFR-SEC-03: basic brute-force mitigation on the login endpoint."""
    scope = 'login'


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

@api_view(['GET'])
@permission_classes([AllowAny])
def csrf_token_view(request):
    """Lets the front-end JS fetch a CSRF token before making POST requests."""
    return Response({'csrfToken': get_token(request)})


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    otp = user.profile.generate_otp()

    send_email(
        user.email,
        'Make a trip OTP',
        'OTP : ' + str(otp)
    )

    return Response(
        {'message': 'Account created. Check your email for a verification code.', 'email': user.email},
        status=status.HTTP_201_CREATED,
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp_view(request):
    serializer = VerifyOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        user = User.objects.get(email__iexact=data['email'])
    except User.DoesNotExist:
        return Response({'detail': 'No account with this email.'}, status=status.HTTP_404_NOT_FOUND)

    profile = user.profile
    if profile.is_email_verified:
        return Response({'message': 'Email already verified. You can log in.'})

    if not profile.otp_is_valid(data['otp_code']):
        return Response({'detail': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)

    profile.is_email_verified = True
    profile.otp_code = ''
    profile.save(update_fields=['is_email_verified', 'otp_code'])
    user.is_active = True
    user.save(update_fields=['is_active'])
    return Response({'message': 'Email verified. You can now log in.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp_view(request):
    serializer = ResendOTPSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        user = User.objects.get(email__iexact=serializer.validated_data['email'])
    except User.DoesNotExist:
        return Response({'detail': 'No account with this email.'}, status=status.HTTP_404_NOT_FOUND)

    if user.profile.is_email_verified:
        return Response({'message': 'Email already verified. You can log in.'})

    otp = user.profile.generate_otp()
    send_email(
        user.email,
        'Make a trip OTP',
        'OTP : ' + str(otp)
    )
    return Response({'message': 'A new code has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    user = authenticate(request, username=email, password=password)
    if user is None:
        try:
            pending = User.objects.get(email__iexact=email)
            if not pending.is_active:
                return Response(
                    {'detail': 'Please verify your email before logging in.', 'unverified': True},
                    status=status.HTTP_403_FORBIDDEN,
                )
        except User.DoesNotExist:
            pass
        return Response({'detail': 'Invalid email or password.'}, status=status.HTTP_400_BAD_REQUEST)

    login(request, user)
    return Response({
        'message': 'Logged in.',
        'is_admin': user.is_staff,
        'full_name': getattr(user.profile, 'full_name', user.username),
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out.'})


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def profile_view(request):
    profile = request.user.profile
    if request.method == 'GET':
        return Response(ProfileSerializer(profile).data)

    serializer = ProfileSerializer(profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        user = User.objects.get(email__iexact=serializer.validated_data['email'])
    except User.DoesNotExist:
        # Don't reveal whether the email exists.
        return Response({'message': 'If that email exists, a reset code has been sent.'})

    otp = user.profile.generate_otp()
    send_email(
        user.email,
        'reset your password',
        'OTP : ' + str(otp)
    )
    return Response({'message': 'If that email exists, a reset code has been sent.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        user = User.objects.get(email__iexact=data['email'])
    except User.DoesNotExist:
        return Response({'detail': 'Invalid code.'}, status=status.HTTP_400_BAD_REQUEST)

    profile = user.profile
    if not profile.otp_is_valid(data['otp_code']):
        return Response({'detail': 'Invalid or expired code.'}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(data['new_password'])
    user.is_active = True
    user.save()
    profile.otp_code = ''
    profile.save(update_fields=['otp_code'])
    return Response({'message': 'Password reset. You can now log in.'})
