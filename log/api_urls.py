from .views import AuditLogViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = router.urls