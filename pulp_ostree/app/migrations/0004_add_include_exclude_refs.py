# Generated by Django 3.2.12 on 2022-03-22 15:38

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ostree', '0003_create_many_to_many_objs_commits'),
    ]

    operations = [
        migrations.AddField(
            model_name='ostreeremote',
            name='exclude_refs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, null=True), null=True, size=None),
        ),
        migrations.AddField(
            model_name='ostreeremote',
            name='include_refs',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=255, null=True), null=True, size=None),
        ),
    ]