# Generated by Django 5.0.6 on 2024-07-08 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_event_lat_event_lon'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='tags',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]