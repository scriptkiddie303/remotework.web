# Generated by Django 3.2.12 on 2025-05-17 09:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('firstapp', '0006_alter_video_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='videos/'),
        ),
    ]
