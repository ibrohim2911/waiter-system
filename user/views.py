# user/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer, PinLoginSerializer
# Import UserSerializer from the correct location

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving users (read-only).
    User creation/management might be handled via admin or a separate mechanism.
    """
    queryset = User.objects.all().order_by('name')
    serializer_class = UserSerializer
    # Only admins can view user list/details via API
    permission_classes = [permissions.IsAdminUser]

class PinLoginAPIView(APIView):
    """
    API endpoint to handle PIN-based login and return a JWT token.
    """
    permission_classes = [permissions.AllowAny] # Anyone can attempt login

    def post(self, request):
        serializer = PinLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True) # Validate PIN
        pin = serializer.validated_data['pin']

        user = authenticate(request, pin=pin)
        if user:
            if user.role not in ["waiter", "accountant"]:
                return Response({'error': 'PIN login is not allowed for this user.'}, status=status.HTTP_401_UNAUTHORIZED)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid PIN'}, status=status.HTTP_401_UNAUTHORIZED)
