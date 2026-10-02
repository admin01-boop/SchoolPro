import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_profiles_for_existing_staff(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    StaffMember = apps.get_model('staff', 'StaffMember')
    for user in User.objects.filter(role='STAFF', staff_profile__isnull=True):
        StaffMember.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='StaffMember',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('employee_id', models.CharField(blank=True, max_length=20, null=True, unique=True)),
                ('hire_date', models.DateField(blank=True, null=True)),
                ('job_title', models.CharField(blank=True, max_length=100)),
                ('department', models.CharField(blank=True, max_length=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='staff_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.RunPython(create_profiles_for_existing_staff, migrations.RunPython.noop),
    ]
