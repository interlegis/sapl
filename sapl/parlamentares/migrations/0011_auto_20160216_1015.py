# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0010_auto_20160107_1850'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dependente',
            name='cpf',
            field=models.CharField(verbose_name='CPF', max_length=14, blank=True),
        ),
        migrations.AlterField(
            model_name='dependente',
            name='rg',
            field=models.CharField(verbose_name='RG', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='dependente',
            name='titulo_eleitor',
            field=models.CharField(verbose_name='Nº Título Eleitor', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='mandato',
            name='observacao',
            field=models.TextField(verbose_name='Observação', blank=True),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='nome',
            field=models.CharField(max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='regiao',
            field=models.CharField(blank=True, choices=[('CO', 'Centro-Oeste'), ('NE', 'Nordeste'), ('NO', 'Norte'), ('SE', 'Sudeste'), ('SL', 'Sul'), ('EX', 'Exterior')], max_length=2),
        ),
        migrations.AlterField(
            model_name='municipio',
            name='uf',
            field=models.CharField(blank=True, choices=[('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'), ('PR', 'Paraná'), ('PB', 'Paraíba'), ('PA', 'Pará'), ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'), ('SE', 'Sergipe'), ('SP', 'São Paulo'), ('TO', 'Tocantins'), ('EX', 'Exterior')], max_length=2),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='biografia',
            field=models.TextField(verbose_name='Biografia', blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='cep_residencia',
            field=models.CharField(verbose_name='CEP', max_length=9, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='cpf',
            field=models.CharField(verbose_name='C.P.F', max_length=14, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='email',
            field=models.CharField(verbose_name='Correio Eletrônico', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='endereco_residencia',
            field=models.CharField(verbose_name='Endereço Residencial', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='endereco_web',
            field=models.CharField(verbose_name='HomePage', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='fax',
            field=models.CharField(verbose_name='Fax', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='fax_residencia',
            field=models.CharField(verbose_name='Fax Residencial', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='locais_atuacao',
            field=models.CharField(verbose_name='Locais de Atuação', max_length=100, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='numero_gab_parlamentar',
            field=models.CharField(verbose_name='Nº Gabinete', max_length=10, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='profissao',
            field=models.CharField(verbose_name='Profissão', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='rg',
            field=models.CharField(verbose_name='R.G.', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='telefone',
            field=models.CharField(verbose_name='Telefone', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='telefone_residencia',
            field=models.CharField(verbose_name='Telefone Residencial', max_length=50, blank=True),
        ),
        migrations.AlterField(
            model_name='parlamentar',
            name='titulo_eleitor',
            field=models.CharField(verbose_name='Título de Eleitor', max_length=15, blank=True),
        ),
        migrations.AlterField(
            model_name='tipoafastamento',
            name='dispositivo',
            field=models.CharField(verbose_name='Dispositivo', max_length=50, blank=True),
        ),
    ]
