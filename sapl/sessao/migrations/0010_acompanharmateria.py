# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0013_remove_tramitacao_ultima'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('sessao', '0009_auto_20151005_0934'),
    ]

    operations = [
        migrations.CreateModel(
            name='AcompanharMateria',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('email', models.CharField(verbose_name='Endereço de email', max_length=50)),
                ('data_cadastro', models.DateField(auto_now_add=True)),
                ('materia_cadastrada', models.ForeignKey(to='materia.MateriaLegislativa')),
                ('usuario', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
