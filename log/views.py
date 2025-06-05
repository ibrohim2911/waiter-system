from django.shortcuts import render
from .models import AuditLog
from rest_framework import viewsets
from .serializers import AuditLogSerializer
from rest_framework import permissions
# Create your views here.

class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]