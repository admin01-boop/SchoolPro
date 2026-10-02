from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_alter_user_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='ui_language',
            field=models.CharField(
                choices=[('en', 'English'), ('km', 'Khmer')],
                default='en',
                max_length=5,
            ),
        ),
    ]