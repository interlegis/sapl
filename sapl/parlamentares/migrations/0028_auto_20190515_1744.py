# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-15 20:44
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0027_auto_20190517_1050'),
    ]

    operations = [
        migrations.RunSQL("""
        UPDATE base_autor SET content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'parlamentares' AND model = 'bloco')
        WHERE content_type_id = (SELECT id FROM django_content_type WHERE app_label = 'sessao' AND model = 'bloco');
        """)
    ]
