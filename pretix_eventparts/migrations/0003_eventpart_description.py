# Generated by Django 3.2.7 on 2021-10-28 21:30

from django.db import migrations
import i18nfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pretix_eventparts', '0002_eventpart_event'),
    ]

    operations = [
        migrations.AddField(
            model_name='eventpart',
            name='description',
            field=i18nfield.fields.I18nCharField(default=''),
        ),
    ]
