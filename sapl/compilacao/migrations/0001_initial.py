# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('norma', '0003_auto_20150906_0239'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dispositivo',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('ordem', models.PositiveIntegerField(verbose_name='Ordem de Renderização', default=0)),
                ('ordem_bloco_atualizador', models.PositiveIntegerField(verbose_name='Ordem de Renderização no Bloco Atualizador', default=0)),
                ('nivel', models.PositiveIntegerField(blank=True, null=True, verbose_name='Nível Estrutural', default=0)),
                ('dispositivo0', models.PositiveIntegerField(verbose_name='Número do Dispositivo', default=0)),
                ('dispositivo1', models.PositiveIntegerField(blank=True, null=True, verbose_name='Primeiro Nível de Variação', default=0)),
                ('dispositivo2', models.PositiveIntegerField(blank=True, null=True, verbose_name='Segundo Nível de Variação', default=0)),
                ('dispositivo3', models.PositiveIntegerField(blank=True, null=True, verbose_name='Terceiro Nível de Variação', default=0)),
                ('dispositivo4', models.PositiveIntegerField(blank=True, null=True, verbose_name='Quarto Nível de Variação', default=0)),
                ('dispositivo5', models.PositiveIntegerField(blank=True, null=True, verbose_name='Quinto Nível de Variação', default=0)),
                ('rotulo', models.CharField(blank=True, max_length=50, verbose_name='Rótulo', default='')),
                ('texto', models.TextField(blank=True, verbose_name='Texto', default='')),
                ('texto_atualizador', models.TextField(blank=True, verbose_name='Texto no Dispositivo Atualizador', default='')),
                ('inicio_vigencia', models.DateField(verbose_name='Início de Vigência')),
                ('fim_vigencia', models.DateField(blank=True, null=True, verbose_name='Fim de Vigência')),
                ('inicio_eficacia', models.DateField(verbose_name='Início de Eficácia')),
                ('fim_eficacia', models.DateField(blank=True, null=True, verbose_name='Fim de Eficácia')),
                ('inconstitucionalidade', models.BooleanField(verbose_name='Inconstitucionalidade', default=False, choices=[(True, 'Sim'), (False, 'Não')])),
                ('visibilidade', models.BooleanField(verbose_name='Visibilidade na Norma Publicada', default=False, choices=[(True, 'Sim'), (False, 'Não')])),
                ('timestamp', models.DateTimeField()),
                ('dispositivo_atualizador', models.ForeignKey(blank=True, null=True, to='compilacao.Dispositivo', verbose_name='Dispositivo Atualizador', default=None, related_name='dispositivo_dispositivo_atualizador')),
                ('dispositivo_pai', models.ForeignKey(blank=True, null=True, to='compilacao.Dispositivo', verbose_name='Dispositivo Pai', default=None, related_name='dispositivo_dispositivo_pai')),
                ('dispositivo_subsequente', models.ForeignKey(blank=True, null=True, to='compilacao.Dispositivo', verbose_name='Dispositivo Subsequente', default=None, related_name='dispositivo_dispositivo_subsequente')),
                ('dispositivo_substituido', models.ForeignKey(blank=True, null=True, to='compilacao.Dispositivo', verbose_name='Dispositivo Substituido', default=None, related_name='dispositivo_dispositivo_substituido')),
                ('dispositivo_vigencia', models.ForeignKey(blank=True, null=True, to='compilacao.Dispositivo', verbose_name='Dispositivo de Vigência', default=None, related_name='dispositivo_dispositivo_vigencia')),
                ('norma', models.ForeignKey(to='norma.NormaJuridica', verbose_name='Norma Jurídica')),
                ('norma_publicada', models.ForeignKey(blank=True, null=True, to='norma.NormaJuridica', verbose_name='Norma Jurídica Publicada', default=None, related_name='dispositivo_norma_publicada')),
            ],
            options={
                'verbose_name': 'Dispositivo',
                'verbose_name_plural': 'Dispositivos',
            },
        ),
        migrations.CreateModel(
            name='Nota',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('texto', models.TextField(verbose_name='Texto da Nota')),
                ('url_externa', models.CharField(blank=True, max_length=1024, verbose_name='Url externa')),
                ('data_criacao', models.DateTimeField(verbose_name='Data de Criação')),
                ('publicacao', models.DateTimeField(verbose_name='Data de Publicação')),
                ('efetifidade', models.DateTimeField(verbose_name='Data de Efeito')),
                ('publicidade', models.PositiveSmallIntegerField(verbose_name='Nível de Publicidade', choices=[(1, 'Nota Privada'), (2, 'Nota Setorial'), (3, 'Nota Institucional'), (4, 'Nota Pública')])),
                ('dispositivo', models.ForeignKey(to='compilacao.Dispositivo', verbose_name='Dispositivo da Nota')),
                ('owner', models.ForeignKey(to=settings.AUTH_USER_MODEL, verbose_name='Dono da Nota')),
            ],
            options={
                'verbose_name': 'Nota',
                'verbose_name_plural': 'Notas',
            },
        ),
        migrations.CreateModel(
            name='Publicacao',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('publicacao', models.DateTimeField(verbose_name='Data de Publicação')),
                ('pagina_inicio', models.PositiveIntegerField(blank=True, null=True, verbose_name='Pg. Início')),
                ('pagina_fim', models.PositiveIntegerField(blank=True, null=True, verbose_name='Pg. Fim')),
                ('timestamp', models.DateTimeField()),
                ('norma', models.ForeignKey(to='norma.NormaJuridica', verbose_name='Norma Jurídica')),
            ],
            options={
                'verbose_name': 'Publicação',
                'verbose_name_plural': 'Publicações',
            },
        ),
        migrations.CreateModel(
            name='TipoDispositivo',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome', unique=True)),
                ('class_css', models.CharField(max_length=20, verbose_name='Classe CSS')),
                ('rotulo_prefixo_html', models.CharField(blank=True, max_length=100, verbose_name='Prefixo html do rótulo')),
                ('rotulo_prefixo_texto', models.CharField(blank=True, max_length=30, verbose_name='Prefixo de construção do rótulo')),
                ('rotulo_ordinal', models.IntegerField(verbose_name='Tipo de número do rótulo')),
                ('rotulo_separadores_variacao', models.CharField(blank=True, max_length=5, verbose_name='Separadores das Variações')),
                ('rotulo_sufixo_texto', models.CharField(blank=True, max_length=30, verbose_name='Sufixo de construção do rótulo')),
                ('rotulo_sufixo_html', models.CharField(blank=True, max_length=100, verbose_name='Sufixo html do rótulo')),
                ('texto_prefixo_html', models.CharField(blank=True, max_length=100, verbose_name='Prefixo html do texto')),
                ('texto_sufixo_html', models.CharField(blank=True, max_length=100, verbose_name='Sufixo html do texto')),
                ('nota_automatica_prefixo_html', models.CharField(blank=True, max_length=100, verbose_name='Prefixo html da nota automática')),
                ('nota_automatica_sufixo_html', models.CharField(blank=True, max_length=100, verbose_name='Sufixo html da nota automática')),
                ('contagem_continua', models.BooleanField(verbose_name='Contagem contínua', choices=[(True, 'Sim'), (False, 'Não')])),
                ('formato_variacao0', models.CharField(max_length=1, verbose_name='Formato da Numeração', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
                ('formato_variacao1', models.CharField(max_length=1, verbose_name='Formato da Variação 1', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
                ('formato_variacao2', models.CharField(max_length=1, verbose_name='Formato da Variação 2', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
                ('formato_variacao3', models.CharField(max_length=1, verbose_name='Formato da Variação 3', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
                ('formato_variacao4', models.CharField(max_length=1, verbose_name='Formato da Variação 4', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
                ('formato_variacao5', models.CharField(max_length=1, verbose_name='Formato da Variação 5', default='1', choices=[('1', '(1) Numérico'), ('I', '(I) Romano Maiúsculo'), ('i', '(i) Romano Minúsculo'), ('A', '(A) Alfabético Maiúsculo'), ('a', '(a) Alfabético Minúsculo'), ('*', 'Tópico - Sem contagem'), ('N', 'Sem renderização')])),
            ],
            options={
                'verbose_name': 'Tipo de Dispositivo',
                'verbose_name_plural': 'Tipos de Dispositivo',
            },
        ),
        migrations.CreateModel(
            name='TipoNota',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla', unique=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
                ('modelo', models.TextField(blank=True, verbose_name='Modelo')),
            ],
            options={
                'verbose_name': 'Tipo de Nota',
                'verbose_name_plural': 'Tipos de Nota',
            },
        ),
        migrations.CreateModel(
            name='TipoPublicacao',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla', unique=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Tipo de Publicação',
                'verbose_name_plural': 'Tipos de Publicação',
            },
        ),
        migrations.CreateModel(
            name='TipoVide',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla', unique=True)),
                ('nome', models.CharField(max_length=50, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Tipo de Vide',
                'verbose_name_plural': 'Tipos de Vide',
            },
        ),
        migrations.CreateModel(
            name='VeiculoPublicacao',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('sigla', models.CharField(max_length=10, verbose_name='Sigla', unique=True)),
                ('nome', models.CharField(max_length=60, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Veículo de Publicação',
                'verbose_name_plural': 'Veículos de Publicação',
            },
        ),
        migrations.CreateModel(
            name='Vide',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('data_criacao', models.DateTimeField(verbose_name='Data de Criação')),
                ('texto', models.TextField(verbose_name='Texto do Vide')),
                ('dispositivo_base', models.ForeignKey(to='compilacao.Dispositivo', verbose_name='Dispositivo Base', related_name='vide_dispositivo_base')),
                ('dispositivo_ref', models.ForeignKey(to='compilacao.Dispositivo', verbose_name='Dispositivo Referido', related_name='vide_dispositivo_ref')),
                ('tipo', models.ForeignKey(to='compilacao.TipoVide', verbose_name='Tipo do Vide')),
            ],
            options={
                'verbose_name': 'Vide',
                'verbose_name_plural': 'Vides',
            },
        ),
        migrations.AddField(
            model_name='publicacao',
            name='tipo_publicacao',
            field=models.ForeignKey(to='compilacao.TipoPublicacao', verbose_name='Tipo de Publicação'),
        ),
        migrations.AddField(
            model_name='publicacao',
            name='veiculo_publicacao',
            field=models.ForeignKey(to='compilacao.VeiculoPublicacao', verbose_name='Veículo de Publicação'),
        ),
        migrations.AddField(
            model_name='nota',
            name='tipo',
            field=models.ForeignKey(to='compilacao.TipoNota', verbose_name='Tipo da Nota'),
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='publicacao',
            field=models.ForeignKey(blank=True, null=True, to='compilacao.Publicacao', verbose_name='Publicação', default=None),
        ),
        migrations.AddField(
            model_name='dispositivo',
            name='tipo_dispositivo',
            field=models.ForeignKey(to='compilacao.TipoDispositivo', verbose_name='Tipo do Dispositivo'),
        ),
        migrations.AlterUniqueTogether(
            name='dispositivo',
            unique_together=set([('norma', 'dispositivo0', 'dispositivo1', 'dispositivo2', 'dispositivo3', 'dispositivo4', 'dispositivo5', 'tipo_dispositivo', 'dispositivo_pai', 'publicacao'), ('norma', 'ordem')]),
        ),
    ]
