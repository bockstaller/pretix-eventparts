# Generated by Django 3.2.8 on 2021-10-29 11:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("pretix_eventparts", "0004_auto_20211028_2252"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventpart",
            name="capacity",
            field=models.IntegerField(default=0),
        ),
    ]
