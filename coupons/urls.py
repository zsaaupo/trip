from django.urls import path
from . import views

urlpatterns = [
    path('', views.coupon_list_create, name='api-coupons-list-create'),
    path('mine/', views.my_coupons, name='api-coupons-mine'),
    path('validate/', views.validate_coupon, name='api-coupons-validate'),
    path('<int:pk>/', views.coupon_detail, name='api-coupons-detail'),
]
