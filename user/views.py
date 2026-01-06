# user/views.py
from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ParseError
from django.contrib.auth import logout as django_logout
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, login
from .models import User
from .serializers import UserSerializer, PinLoginSerializer, ChangePasswordSerializer, PhonePasswordLoginSerializer
# Import UserSerializer from the correct location
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint for full CRUD on users.
    Restricted to admin users for create/update/delete/list operations.
    """
    queryset = User.objects.all().order_by('name')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

@method_decorator(csrf_exempt, name='dispatch')
class PinLoginAPIView(APIView):
    """
    API endpoint to handle PIN-based login and return a JWT token.
    """
    authentication_classes = []
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
                'user_id': user.id,
                'user_name': user.name,
                'role': user.role,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid PIN'}, status=status.HTTP_401_UNAUTHORIZED)
from django.middleware.csrf import get_token

class PhonePasswordJWTLoginAPIView(APIView):
    """
    API endpoint for phone/password login that returns JWT tokens.
    """
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    serializer_class = PhonePasswordLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data.get('phone_number')
        password = serializer.validated_data.get('password')

        user = authenticate(request, username=phone_number, password=password)
        if user is not None:
            if not user.is_active:
                return Response({'error': 'User is inactive.'}, status=status.HTTP_403_FORBIDDEN)
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'user_name': user.name,
                'phone_number': user.phone_number,
                'role': user.role,
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

class PhonePasswordLoginAPIView(APIView):
    """
    API endpoint for phone/password login using session authentication.
    Requires CSRF token.
    """
    authentication_classes = []  # Allow unauthenticated access
    permission_classes = []      # Allow anyone to attempt login

    def post(self, request):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')
        if not phone_number or not password:
            return Response({'error': 'phone_number and password required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=phone_number, password=password)
        if user is not None:
            if not user.is_active:
                return Response({'error': 'User is inactive.'}, status=status.HTTP_403_FORBIDDEN)
            login(request, user)  # Sets session
            # Optionally return user info or just success
            return Response({'success': True, 'user_id': user.id, 'csrf_token': get_token(request)})
        else:
            return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPIView(APIView):
    """Blacklist a refresh token on logout (logout for JWT clients).

    Accepts POST with JSON: { "refresh": "<refresh_token>" }
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            raise ParseError('`refresh` token is required in request body.')

        try:
            token = RefreshToken(refresh_token)
            # Blacklist the refresh token
            token.blacklist()
        except Exception as e:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        # Also log out any session if present
        try:
            django_logout(request)
        except Exception:
            pass

        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def getmeview(request):
    """
    Simple view to return current authenticated user's info.
    """
    if request.user.is_authenticated:
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    else:
        return Response({'error': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)

class ChangePasswordView(generics.UpdateAPIView):
    """
    An endpoint for changing password for authenticated users.
    """
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"detail": "Password updated successfully"}, status=status.HTTP_200_OK)
        
from .serializers import CustomLoginS
class LoginView2(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        ser = CustomLoginS(data=request.data)
        ser.is_valid(raise_exception=True)
        get_token = ser.validated_data['token']
        return Response(get_token, status=status.HTTP_200_OK)