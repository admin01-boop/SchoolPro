from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AdminProfile, Observer, StaffMember, Teacher

PROFILE_MODEL_BY_ROLE = {
    'TEACHER': Teacher,
    'STAFF': StaffMember,
    'OBSERVER': Observer,
    'ADMIN': AdminProfile,
}


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_role_profile(sender, instance, raw=False, **kwargs):
    """Every user in a role with a profile table gets a profile row, whichever way the user was created."""
    model = PROFILE_MODEL_BY_ROLE.get(instance.role)
    if model and not raw:
        model.objects.get_or_create(user=instance)
