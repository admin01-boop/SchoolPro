import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_profiles_for_existing_admins(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    AdminProfile = apps.get_model('staff', 'AdminProfile')
    for user in User.objects.filter(role='ADMIN', admin_profile__isnull=True):
        AdminProfile.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0003_observer'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AdminProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('job_title', models.CharField(blank=True, max_length=100)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.RunPython(create_profiles_for_existing_admins, migrations.RunPython.noop),
    ]
