# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CasaLegislativa',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nome', models.CharField(max_length=100, verbose_name='Nome')),
                ('sigla', models.CharField(max_length=100, verbose_name='Sigla')),
                ('endereco', models.CharField(max_length=100, verbose_name='Endere\xe7o')),
                ('cep', models.CharField(max_length=100, verbose_name='CEP')),
                ('municipio', models.CharField(max_length=100, verbose_name='Munic\xedpio')),
                ('uf', models.CharField(max_length=100, verbose_name='UF')),
                ('telefone', models.CharField(max_length=100, verbose_name='Telefone')),
                ('fax', models.CharField(max_length=100, verbose_name='Fax')),
                ('cor_fundo', models.CharField(max_length=100, verbose_name='Cor de fundo')),
                ('cor_borda', models.CharField(max_length=100, verbose_name='Cor da borda')),
                ('cor_principal', models.CharField(max_length=100, verbose_name='Cor principal')),
                ('logotipo', models.CharField(max_length=100, verbose_name='Logotipo')),
                ('endereco_web', models.CharField(max_length=100, verbose_name='HomePage')),
                ('email', models.CharField(max_length=100, verbose_name='E-mail')),
                ('informacao_geral', models.CharField(max_length=100, verbose_name='Informa\xe7\xe3o Geral')),
            ],
            options={
                'verbose_name': 'Casa Legislativa',
                'verbose_name_plural': 'Casas Legislativas',
            },
        ),
    ]
