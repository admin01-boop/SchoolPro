from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('STUDENT', 'Students'),
                    ('TEACHER', 'Teachers & Advisors'),
                    ('PARENT', 'Parents'),
                    ('OBSERVER', 'Observers'),
                    ('ADMIN', 'Admins'),
                    ('STAFF', 'Staff'),
                ],
                default='STAFF',
                max_length=20,
            ),
        ),
    ]