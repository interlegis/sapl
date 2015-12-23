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
                ('id', models.AutoField(
                    auto_created=True, serialize=False, primary_key=True,
                    verbose_name='ID')),
                ('sigla', models.CharField(
                    unique=True, max_length=10, verbose_name='Sigla')),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('padrao', models.BooleanField(
                    choices=[(True, 'Sim'), (False, 'Não')], default=False,
                    verbose_name='Padrão')),
            ],
            options={
                'verbose_name_plural': 'Perfis Estruturais de'
                ' Textos Articulados',
                'verbose_name': 'Perfil Estrutural de Texto Articulado',
                'ordering': ['-padrao', 'sigla'],
            },
        ),
        migrations.CreateModel(
            name='TextoArticulado',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    serialize=False, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(
                    auto_now_add=True, verbose_name='created')),
                ('modified', models.DateTimeField(
                    auto_now=True, verbose_name='modified')),
                ('data', models.DateField(
                    blank=True, null=True, verbose_name='Data')),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('observacao', models.TextField(
                    blank=True, null=True, verbose_name='Observação')),
                ('numero', models.PositiveIntegerField(verbose_name='Número')),
                ('ano', models.PositiveSmallIntegerField(verbose_name='Ano')),
            ],
            options={
                'verbose_name_plural': 'Textos Articulados',
                'verbose_name': 'Texto Articulado',
            },
        ),
        migrations.AlterModelOptions(
            name='dispositivo',
            options={'verbose_name_plural': 'Dispositivos',
                     'verbose_name': 'Dispositivo'},
        ),
        migrations.RemoveField(
            model_name='publicacao',
            name='norma',
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='visibilidade',
            field=models.BooleanField(choices=[(
                True, 'Sim'), (False, 'Não')], default=False,
                verbose_name='Visibilidade no Texto Articulado Publicado'),
        ),
        migrations.AlterField(
            model_name='tipodispositivorelationship',
            name='perfil',
            field=models.ForeignKey(
                to='compilacao.PerfilEstruturalTextoArticulado'),
        ),
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([]),
        ),
        migrations.DeleteModel(
            name='PerfilEstruturalTextosNormativos',
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
            field=models.ForeignKey(
                related_name='dispositivos_set',
                verbose_name='Texto Articulado',
                to='compilacao.TextoArticulado', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='ta_publicado',
            field=models.ForeignKey(
                related_name='dispositivos_alterados_pelo_ta_set', blank=True,
                verbose_name='Texto Articulado Publicado',
                default=None, to='compilacao.TextoArticulado', null=True),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='ta',
            field=models.ForeignKey(
                verbose_name='Texto Articulado',
                to='compilacao.TextoArticulado', default=1),
            preserve_default=False,
        ),
    ]
