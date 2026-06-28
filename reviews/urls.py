from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_reviews, name='api-reviews-list'),
    path('create/', views.create_review, name='api-reviews-create'),
    path('pending/', views.pending_reviews, name='api-reviews-pending'),
    path('<int:review_id>/moderate/', views.moderate_review, name='api-reviews-moderate'),
]
