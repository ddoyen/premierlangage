# Generated by Django 2.0.6 on 2018-09-05 13:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=1024, unique=True)),
                ('remote', models.CharField(blank=True, default='', max_length=1024)),
                ('root', models.CharField(blank=True, max_length=1024)),
                ('public', models.BooleanField(default=False)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('read_auth', models.ManyToManyField(blank=True, related_name='dir_read_auth', to=settings.AUTH_USER_MODEL)),
                ('write_auth', models.ManyToManyField(blank=True, related_name='dir_write_auth', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
