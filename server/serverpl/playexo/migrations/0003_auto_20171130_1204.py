# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-30 12:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gitload', '0003_auto_20171117_1538'),
        ('playexo', '0002_auto_20171117_1538'),
    ]

    operations = [
        migrations.CreateModel(
            name='ActivityTest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('pltp', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gitload.PLTP')),
            ],
        ),
        migrations.AlterField(
            model_name='activity',
            name='id',
            field=models.IntegerField(primary_key=True, serialize=False),
        ),
    ]
