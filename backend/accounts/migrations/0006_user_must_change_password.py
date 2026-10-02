from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_alter_user_managers_alter_historicaluser_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaluser',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='user',
            name='must_change_password',
            field=models.BooleanField(default=False),
        ),
    ]