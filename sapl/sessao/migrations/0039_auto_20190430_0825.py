# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-30 11:25
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0038_merge_20190415_1800'),
    ]

    database_operations = [migrations.AlterModelTable('Bloco', 'parlamentares_bloco')]

    state_operations = [migrations.DeleteModel('Bloco')]

    operations = [
      migrations.SeparateDatabaseAndState(
        database_operations=database_operations,
        state_operations=state_operations)
    ]