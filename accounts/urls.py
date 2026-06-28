from django.urls import path
from . import views

urlpatterns = [
    path('csrf/', views.csrf_token_view, name='api-csrf'),
    path('register/', views.register_view, name='api-register'),
    path('verify-otp/', views.verify_otp_view, name='api-verify-otp'),
    path('resend-otp/', views.resend_otp_view, name='api-resend-otp'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('profile/', views.profile_view, name='api-profile'),
    path('password-reset/', views.password_reset_request_view, name='api-password-reset'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='api-password-reset-confirm'),
]
