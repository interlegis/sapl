# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('norma', '0009_auto_20160106_1511'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assuntonorma',
            name='descricao',
            field=models.CharField(verbose_name='Descrição', max_length=250, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='alinea',
            field=models.CharField(verbose_name='Alínea', max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='artigo',
            field=models.CharField(verbose_name='Artigo', max_length=4, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='capitulo',
            field=models.CharField(verbose_name='Capítulo', max_length=7, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='disposicoes',
            field=models.CharField(verbose_name='Disposição', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='inciso',
            field=models.CharField(verbose_name='Inciso', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='item',
            field=models.CharField(verbose_name='Item', max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='livro',
            field=models.CharField(verbose_name='Livro', max_length=7, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='paragrafo',
            field=models.CharField(verbose_name='Parágrafo', max_length=3, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='parte',
            field=models.CharField(verbose_name='Parte', max_length=8, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='secao',
            field=models.CharField(verbose_name='Seção', max_length=7, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='subsecao',
            field=models.CharField(verbose_name='Subseção', max_length=7, blank=True),
        ),
        migrations.AlterField(
            model_name='legislacaocitada',
            name='titulo',
            field=models.CharField(verbose_name='Título', max_length=7, blank=True),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='indexacao',
            field=models.TextField(verbose_name='Indexação', blank=True),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='observacao',
            field=models.TextField(verbose_name='Observação', blank=True),
        ),
        migrations.AlterField(
            model_name='normajuridica',
            name='veiculo_publicacao',
            field=models.CharField(verbose_name='Veículo Publicação', max_length=30, blank=True),
        ),
        migrations.AlterField(
            model_name='tiponormajuridica',
            name='equivalente_lexml',
            field=models.CharField(blank=True, verbose_name='Equivalente LexML', choices=[('constituicao', 'constituicao'), ('ementa.constitucional', 'ementa.constitucional'), ('lei.complementar', 'lei.complementar'), ('lei.delegada', 'lei.delegada'), ('lei', 'lei'), ('decreto.lei', 'decreto.lei'), ('medida.provisoria', 'medida.provisoria'), ('decreto', 'decreto'), ('lei.organica', 'lei.organica'), ('emenda.lei.organica', 'emenda.lei.organica'), ('decreto.legislativo', 'decreto.legislativo'), ('resolucao', 'resolucao'), ('regimento.interno', 'regimento.interno')], max_length=50),
        ),
        migrations.AlterField(
            model_name='vinculonormajuridica',
            name='tipo_vinculo',
            field=models.CharField(blank=True, choices=[('A', 'Altera a norma'), ('R', 'Revoga a norma'), ('P', 'Revoga parcialmente a norma'), ('T', 'Revoga por consolidação a norma'), ('C', 'Norma correlata'), ('I', 'Suspende a execução da norma'), ('G', 'Regulamenta a norma')], max_length=1),
        ),
    ]
