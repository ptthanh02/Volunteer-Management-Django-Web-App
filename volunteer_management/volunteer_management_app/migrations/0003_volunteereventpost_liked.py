# Generated by Django 5.0.3 on 2024-05-15 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('volunteer_management_app', '0002_alter_volunteereventpost_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='volunteereventpost',
            name='liked',
            field=models.BooleanField(default=False),
        ),
    ]