# user/views.py
from .models import User
from rest_framework import viewsets, permissions

# Ensure UserSerializer is correctly defined and imported
try:
    from .serializers import UserSerializer
except ImportError:
    UserSerializer = None

# Only define if UserSerializer was imported successfully
if UserSerializer:
    class UserViewSet(viewsets.ReadOnlyModelViewSet):
        """
        API endpoint for listing and retrieving users (read-only).
        User creation/management might be handled via admin or a separate mechanism.
        """
        queryset = User.objects.all().order_by('name')
        serializer_class = UserSerializer
        # Only admins can view user list/details via API
        permission_classes = [permissions.IsAdminUser]
else:
    # Define a placeholder view if serializer is missing, prevents import errors elsewhere
    from rest_framework.views import APIView
    from rest_framework.response import Response
    class UserViewSet(APIView):
        permission_classes = [permissions.IsAdminUser] # Still protect placeholder
        def get(self, request, *args, **kwargs):
            return Response({"error": "UserSerializer not available"}, status=500)
