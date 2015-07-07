# -*- coding: utf-8 -*-


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
                ('assunto', models.CharField(max_length=50, verbose_name='Assunto')),
                ('descricao', models.CharField(max_length=250, null=True, verbose_name='Descri\xe7\xe3o', blank=True)),
            ],
            options={
                'verbose_name': 'Assunto de Norma',
                'verbose_name_plural': 'Assuntos de Norma',
            },
        ),
        migrations.CreateModel(
            name='LegislacaoCitada',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('disposicoes', models.CharField(max_length=15, null=True, verbose_name='Disposi\xe7\xe3o', blank=True)),
                ('parte', models.CharField(max_length=8, null=True, verbose_name='Parte', blank=True)),
                ('livro', models.CharField(max_length=7, null=True, verbose_name='Livro', blank=True)),
                ('titulo', models.CharField(max_length=7, null=True, verbose_name='T\xedtulo', blank=True)),
                ('capitulo', models.CharField(max_length=7, null=True, verbose_name='Cap\xedtulo', blank=True)),
                ('secao', models.CharField(max_length=7, null=True, verbose_name='Se\xe7\xe3o', blank=True)),
                ('subsecao', models.CharField(max_length=7, null=True, verbose_name='Subse\xe7\xe3o', blank=True)),
                ('artigo', models.CharField(max_length=4, null=True, verbose_name='Artigo', blank=True)),
                ('paragrafo', models.CharField(max_length=3, null=True, verbose_name='Par\xe1grafo', blank=True)),
                ('inciso', models.CharField(max_length=10, null=True, verbose_name='Inciso', blank=True)),
                ('alinea', models.CharField(max_length=3, null=True, verbose_name='Al\xednea', blank=True)),
                ('item', models.CharField(max_length=3, null=True, verbose_name='Item', blank=True)),
                ('materia', models.ForeignKey(to='materia.MateriaLegislativa')),
            ],
            options={
                'verbose_name': 'Mat\xe9ria Legislativa',
                'verbose_name_plural': 'Mat\xe9rias Legislativas',
            },
        ),
        migrations.CreateModel(
            name='NormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('numero', models.IntegerField(verbose_name='N\xfamero')),
                ('ano', models.SmallIntegerField(verbose_name='Ano')),
                ('esfera_federacao', models.CharField(max_length=1, verbose_name='Esfera Federa\xe7\xe3o', choices=[(b'M', 'Municipal'), (b'E', 'Estadual'), (b'F', 'Federal')])),
                ('data', models.DateField(null=True, verbose_name='Data', blank=True)),
                ('data_publicacao', models.DateField(null=True, verbose_name='Data Publica\xe7\xe3o', blank=True)),
                ('veiculo_publicacao', models.CharField(max_length=30, null=True, verbose_name='Ve\xedculo Publica\xe7\xe3o', blank=True)),
                ('pagina_inicio_publicacao', models.IntegerField(null=True, verbose_name='Pg. In\xedcio', blank=True)),
                ('pagina_fim_publicacao', models.IntegerField(null=True, verbose_name='Pg. Fim', blank=True)),
                ('ementa', models.TextField(verbose_name='Ementa')),
                ('indexacao', models.TextField(null=True, verbose_name='Indexa\xe7\xe3o', blank=True)),
                ('observacao', models.TextField(null=True, verbose_name='Observa\xe7\xe3o', blank=True)),
                ('complemento', models.NullBooleanField(verbose_name='Complementar ?')),
                ('data_vigencia', models.DateField(null=True, blank=True)),
                ('timestamp', models.DateTimeField()),
                ('assunto', models.ForeignKey(to='norma.AssuntoNorma')),
                ('materia', models.ForeignKey(blank=True, to='materia.MateriaLegislativa', null=True)),
            ],
            options={
                'verbose_name': 'Norma Jur\xeddica',
                'verbose_name_plural': 'Normas Jur\xeddicas',
            },
        ),
        migrations.CreateModel(
            name='TipoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('equivalente_lexml', models.CharField(blank=True, max_length=50, null=True, verbose_name='Equivalente LexML', choices=[(b'constituicao', b'constituicao'), (b'ementa.constitucional', b'ementa.constitucional'), (b'lei.complementar', b'lei.complementar'), (b'lei.delegada', b'lei.delegada'), (b'lei', b'lei'), (b'decreto.lei', b'decreto.lei'), (b'medida.provisoria', b'medida.provisoria'), (b'decreto', b'decreto'), (b'lei.organica', b'lei.organica'), (b'emenda.lei.organica', b'emenda.lei.organica'), (b'decreto.legislativo', b'decreto.legislativo'), (b'resolucao', b'resolucao'), (b'regimento.interno', b'regimento.interno')])),
                ('sigla', models.CharField(max_length=3, verbose_name='Sigla')),
                ('descricao', models.CharField(max_length=50, verbose_name='Descri\xe7\xe3o')),
            ],
            options={
                'verbose_name': 'Tipo de Norma Jur\xeddica',
                'verbose_name_plural': 'Tipos de Norma Jur\xeddica',
            },
        ),
        migrations.CreateModel(
            name='VinculoNormaJuridica',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tipo_vinculo', models.CharField(blank=True, max_length=1, null=True, choices=[(b'A', 'Altera a norma'), (b'R', 'Revoga a norma'), (b'P', 'Revoga parcialmente a norma'), (b'T', 'Revoga por consolida\xe7\xe3o a norma'), (b'C', 'Norma correlata'), (b'I', 'Suspende a execu\xe7\xe3o da norma'), (b'G', 'Regulamenta a norma')])),
                ('norma_referente', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
                ('norma_referida', models.ForeignKey(related_name='+', to='norma.NormaJuridica')),
            ],
            options={
                'verbose_name': 'V\xednculo entre Normas Jur\xeddicas',
                'verbose_name_plural': 'V\xednculos entre Normas Jur\xeddicas',
            },
        ),
        migrations.AddField(
            model_name='normajuridica',
            name='tipo',
            field=models.ForeignKey(verbose_name='Tipo', to='norma.TipoNormaJuridica'),
        ),
        migrations.AddField(
            model_name='legislacaocitada',
            name='norma',
            field=models.ForeignKey(to='norma.NormaJuridica'),
        ),
    ]
