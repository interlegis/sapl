# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('materia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssuntoNorma',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_assunto', models.CharField(max_length=50)),
                ('descricao_estendida', models.CharField(max_length=250, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('descricao_disposicoes', models.CharField(max_length=15, null=True, blank=True)),
                ('descricao_parte', models.CharField(max_length=8, null=True, blank=True)),
                ('descricao_livro', models.CharField(max_length=7, null=True, blank=True)),
                ('descricao_titulo', models.CharField(max_length=7, null=True, blank=True)),
                ('descricao_capitulo', models.CharField(max_length=7, null=True, blank=True)),
                ('descricao_secao', models.CharField(max_length=7, null=True, blank=True)),
                ('descricao_subsecao', models.CharField(max_length=7, null=True, blank=True)),
                ('descricao_artigo', models.CharField(max_length=4, null=True, blank=True)),
                ('descricao_paragrafo', models.CharField(max_length=3, null=True, blank=True)),
                ('descricao_inciso', models.CharField(max_length=10, null=True, blank=True)),
                ('descricao_alinea', models.CharField(max_length=3, null=True, blank=True)),
                ('descricao_item', models.CharField(max_length=3, null=True, blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero_norma', models.IntegerField()),
                ('ano_norma', models.SmallIntegerField()),
                ('tipo_esfera_federacao', models.CharField(max_length=1)),
                ('data_norma', models.DateField(null=True, blank=True)),
                ('data_publicacao', models.DateField(null=True, blank=True)),
                ('descricao_veiculo_publicacao', models.CharField(max_length=30, null=True, blank=True)),
                ('numero_pag_inicio_publ', models.IntegerField(null=True, blank=True)),
                ('numero_pag_fim_publ', models.IntegerField(null=True, blank=True)),
                ('txt_ementa', models.TextField()),
                ('txt_indexacao', models.TextField(null=True, blank=True)),
                ('txt_observacao', models.TextField(null=True, blank=True)),
                ('complemento', models.NullBooleanField()),
                ('data_vigencia', models.DateField(null=True, blank=True)),
                ('timestamp', models.DateTimeField()),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
                ('materia', models.ForeignKey(blank=True, to='materia.MateriaLegislativa', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('voc_lexml', models.CharField(max_length=50, null=True, blank=True)),
                ('sigla_tipo_norma', models.CharField(max_length=3)),
                ('descricao_tipo_norma', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_vinculo', models.CharField(max_length=1, null=True, blank=True)),
                ('norma_referente', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
                ('norma_referida', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
            ],
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='tipo',
            field=models.ForeignKey(to='norma.TipoNormaJuridica'),
        ),
        migrations.AddField(
            model_name='legislacaocitada',
            name='norma',
            field=models.ForeignKey(to='norma.NormaJuridica'),
        ),
    ]
