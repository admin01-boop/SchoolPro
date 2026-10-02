from django.conf import settings
from django.db import migrations

PROFILE_MODEL_BY_ROLE = {
    'TEACHER': 'Teacher',
    'STAFF': 'StaffMember',
    'OBSERVER': 'Observer',
    'ADMIN': 'AdminProfile',
}


def create_missing_profiles(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    for role, model_name in PROFILE_MODEL_BY_ROLE.items():
        model = apps.get_model('staff', model_name)
        for user in User.objects.filter(role=role).exclude(id__in=model.objects.values('user_id')):
            model.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0004_adminprofile'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(create_missing_profiles, migrations.RunPython.noop),
    ]
