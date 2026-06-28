from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # ----------------------------- REST API ----------------------------- #
    path('api/accounts/', include('accounts.urls')),
    path('api/hotels/', include('hotels.urls')),
    path('api/transport/', include('transportation.urls')),
    path('api/packages/', include('packages.urls')),
    path('api/coupons/', include('coupons.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/dashboard/', include('dashboard.urls')),

    # ------------------------------- Pages -------------------------------- #
    path('', views.home, name='page-home'),

    path('register/', views.register_page, name='page-register'),
    path('verify-otp/', views.verify_otp_page, name='page-verify-otp'),
    path('login/', views.login_page, name='page-login'),
    path('forgot-password/', views.forgot_password_page, name='page-forgot-password'),
    path('reset-password/', views.reset_password_page, name='page-reset-password'),
    path('profile/', views.profile_page, name='page-profile'),

    path('dashboard/', views.dashboard_page, name='page-dashboard'),
    path('admin-dashboard/', views.admin_dashboard_page, name='page-admin-dashboard'),

    path('hotels/', views.hotel_list_page, name='page-hotels-list'),
    path('hotels/<int:pk>/', views.hotel_detail_page, name='page-hotels-detail'),

    path('transport/', views.transport_choose_page, name='page-transport-choose'),
    path('transport/buses/', views.bus_list_page, name='page-buses-list'),
    path('transport/buses/<int:pk>/', views.bus_detail_page, name='page-buses-detail'),
    path('transport/cars/', views.car_list_page, name='page-cars-list'),
    path('transport/cars/<int:pk>/', views.car_detail_page, name='page-cars-detail'),

    path('packages/', views.package_list_page, name='page-packages-list'),
    path('packages/<int:pk>/', views.package_detail_page, name='page-packages-detail'),

    path('bookings/', views.booking_history_page, name='page-bookings-history'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
