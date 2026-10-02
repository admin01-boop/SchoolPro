import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_profiles_for_existing_observers(apps, schema_editor):
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    Observer = apps.get_model('staff', 'Observer')
    for user in User.objects.filter(role='OBSERVER', observer_profile__isnull=True):
        Observer.objects.create(user=user)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0002_staffmember'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Observer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('organization', models.CharField(blank=True, max_length=150)),
                ('phone', models.CharField(blank=True, max_length=30)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='observer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['user__last_name', 'user__first_name'],
            },
        ),
        migrations.RunPython(create_profiles_for_existing_observers, migrations.RunPython.noop),
    ]
