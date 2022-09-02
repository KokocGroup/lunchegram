# Generated by Django 2.2.9 on 2022-09-02 22:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20220903_0138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='employee',
            name='user',
            field=models.ForeignKey(limit_choices_to={'has_telegram': True}, on_delete=django.db.models.deletion.CASCADE, related_name='employees', to=settings.AUTH_USER_MODEL),
        ),
    ]
