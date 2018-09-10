# Generated by Django 2.0.5 on 2018-09-06 18:47

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('classmanagement', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Groups',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('password', models.CharField(blank=True, max_length=1024)),
                ('name', models.CharField(max_length=1024)),
                ('max_members', models.IntegerField(null=True)),
                ('creation_date', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('students', models.ManyToManyField(blank=True, related_name='students', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='RequiredGroups',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=1024)),
                ('max_members', models.IntegerField(null=True)),
                ('limit_date', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='classmanagement.Course')),
                ('groups', models.ManyToManyField(blank=True, related_name='groups', to='groups.Groups')),
            ],
        ),
    ]