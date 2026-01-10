# user/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views # Adjust import if needed
from .api_stats import UserStatsView
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
from django.urls import path
from . import views

urlpatterns = [
    path('config.js', views.config_js, name='config_js'),
    path('', include(router.urls)),
    path('user-stats/', UserStatsView.as_view(), name='user-stats'),
    # New endpoint
    path('pin-login/', views.PinLoginAPIView.as_view(), name='pin-login'),
    path('phone-login/', views.PhonePasswordLoginAPIView.as_view(), name='phone-login'),
    path('phone-jwt-login/', views.PhonePasswordJWTLoginAPIView.as_view(), name='phone-jwt-login'),
    path('logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    path('login/', views.LoginView2.as_view(), name='login')

]
