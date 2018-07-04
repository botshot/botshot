# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Button',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('text', models.CharField(max_length=255, blank=True, null=True)),
                ('action', models.CharField(max_length=255, blank=True, null=True)),
                ('url', models.CharField(max_length=1024, blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('title', models.CharField(max_length=255, blank=True, null=True)),
                ('subtitle', models.CharField(max_length=255, blank=True, null=True)),
                ('image_url', models.CharField(max_length=255, blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('text', models.CharField(max_length=255)),
                ('uid', models.CharField(max_length=255)),
                ('timestamp', models.BigIntegerField()),
                ('is_response', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='element',
            name='message',
            field=models.ForeignKey(to='webgui.Message', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='button',
            name='message',
            field=models.ForeignKey(to='webgui.Message', on_delete=models.CASCADE),
        ),
    ]
