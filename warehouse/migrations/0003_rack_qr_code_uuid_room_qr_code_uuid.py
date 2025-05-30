# Generated by Django 5.2.1 on 2025-05-13 16:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('warehouse', '0002_shelf_qr_code_uuid'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='qr_code_uuid',
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='room',
            name='qr_code_uuid',
            field=models.UUIDField(blank=True, null=True, unique=True),
        ),
    ]
