# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.db import migrations
from sapl.utils import clear_thumbnails_cache


def clear_thumbnails_cache_migrate(apps, schema_editor):
    Parlamentar = apps.get_model("parlamentares", "Parlamentar")
    parlamentares = Parlamentar.objects.all()
    clear_thumbnails_cache(parlamentares, 'fotografia')


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0020_fix_inicio_mandato'),
    ]

    operations = [
        migrations.RunPython(clear_thumbnails_cache_migrate),
    ]
