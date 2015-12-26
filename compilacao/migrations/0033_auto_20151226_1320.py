# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0032_auto_20151213_1538'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerfilEstruturalTextoArticulado',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('sigla', models.CharField(unique=True, max_length=10, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('padrao', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Padrão')),
            ],
            options={
                'verbose_name_plural': 'Perfis Estruturais de Textos Articulados',
                'verbose_name': 'Perfil Estrutural de Texto Articulado',
                'ordering': ['-padrao', 'sigla'],
            },
        ),
        migrations.CreateModel(
            name='TextoArticulado',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('data', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('observacao', models.TextField(null=True, verbose_name='Observação', blank=True)),
                ('numero', models.PositiveIntegerField(verbose_name='Número')),
                ('ano', models.PositiveSmallIntegerField(verbose_name='Ano')),
                ('participacao_social', models.NullBooleanField(choices=[(None, 'Padrão definido no Tipo'), (True, 'Sim'), (False, 'Não')], default=None, verbose_name='Participação Social')),
            ],
            options={
                'verbose_name_plural': 'Textos Articulados',
                'verbose_name': 'Texto Articulado',
                'ordering': ['-data', '-numero'],
            },
        ),
        migrations.CreateModel(
            name='TipoTextoArticulado',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('sigla', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descrição')),
                ('participacao_social', models.NullBooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Participação Social')),
            ],
            options={
                'verbose_name_plural': 'Tipos de Texto Articulados',
                'verbose_name': 'Tipo de Texto Articulado',
            },
        ),
        migrations.AlterModelOptions(
            name='dispositivo',
            options={'verbose_name_plural': 'Dispositivos', 'verbose_name': 'Dispositivo', 'ordering': ['ta', 'ordem']},
        ),
        migrations.RemoveField(
            model_name='publicacao',
            name='norma',
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='visibilidade',
            field=models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Visibilidade no Texto Articulado Publicado'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='perfil',
            field=models.ForeignKey(to='compilacao.PerfilEstruturalTextoArticulado'),
        ),
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([]),
        ),
        migrations.DeleteModel(
            name='PerfilEstruturalTextosNormativos',
        ),
        migrations.AddField(
            model_name='textoarticulado',
            name='tipo_ta',
            field=models.ForeignKey(to='compilacao.TipoTextoArticulado', default=None, blank=True, null=True, verbose_name='Tipo de Texto Articulado'),
        ),
        migrations.RemoveField(
            model_name='dispositivo',
            name='norma',
        ),
        migrations.RemoveField(
            model_name='dispositivo',
            name='norma_publicada',
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='ta',
            field=models.ForeignKey(default=1, to='compilacao.TextoArticulado', related_name='dispositivos_set', verbose_name='Texto Articulado'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='ta_publicado',
            field=models.ForeignKey(to='compilacao.TextoArticulado', default=None, blank=True, null=True, related_name='dispositivos_alterados_pelo_ta_set', verbose_name='Texto Articulado Publicado'),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='ta',
            field=models.ForeignKey(default=1, to='compilacao.TextoArticulado', verbose_name='Texto Articulado'),
            preserve_default=False,
        ),
    ]
