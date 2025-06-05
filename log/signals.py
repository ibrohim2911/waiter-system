from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.forms.models import model_to_dict
from .models import AuditLog
from django.conf import settings

# List all models you want to track
from order.models import Order, OrderItem, MenuItem
from inventory.models import Table, Inventory

def get_user_from_instance(instance):
    # Try to get user from instance if available
    if hasattr(instance, 'user'):
        return instance.user
    return None

def log_change(instance, action, changes=None):
    AuditLog.objects.create(
        model_name=instance.__class__.__name__,
        object_id=str(instance.pk),
        action=action,
        changes=changes,
        user=get_user_from_instance(instance)
    )

@receiver(post_save, sender=Order)
@receiver(post_save, sender=OrderItem)
@receiver(post_save, sender=MenuItem)
@receiver(post_save, sender=Table)
@receiver(post_save, sender=Inventory)
def log_save(sender, instance, created, **kwargs):
    action = 'create' if created else 'update'
    changes = model_to_dict(instance)
    log_change(instance, action, changes)

@receiver(pre_delete, sender=Order)
@receiver(pre_delete, sender=OrderItem)
@receiver(pre_delete, sender=MenuItem)
@receiver(pre_delete, sender=Table)
@receiver(pre_delete, sender=Inventory)
def log_delete(sender, instance, **kwargs):
    changes = model_to_dict(instance)
    log_change(instance, 'delete', changes)