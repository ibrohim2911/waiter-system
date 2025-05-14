# user/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Adjust import if needed

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # New endpoint
    path('pin-login/', views.PinLoginAPIView.as_view(), name='pin-login'),
]
