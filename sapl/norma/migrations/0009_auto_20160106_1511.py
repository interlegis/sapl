# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0008_normajuridica_texto_integral'),
    ]

    operations = [
        migrations.AlterField(
            model_name='normajuridica',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo da Norma Juridica', to='norma.TipoNormaJuridica'),
        ),
    ]
