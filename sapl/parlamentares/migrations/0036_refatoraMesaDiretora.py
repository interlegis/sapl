# Generated by Django 2.2.20 on 2021-07-02 14:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0035_auto_20210315_1522'),
    ]

    operations = [
        migrations.CreateModel(
            name='MesaDiretora',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_inicio', models.DateField(verbose_name='Data Início')),
                ('data_fim', models.DateField(null=True, verbose_name='Data Fim')),
                ('descricao', models.TextField(blank=True, verbose_name='Descrição')),
                ('sessao_legislativa', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.SessaoLegislativa')),
            ],
            options={
                'verbose_name': 'Mesa Diretora',
                'verbose_name_plural': 'Mesas Diretoras',
                'ordering': ('-data_inicio', '-sessao_legislativa'),
            },
        ),
        migrations.AddField(
            model_name='composicaomesa',
            name='mesa_diretora',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='parlamentares.MesaDiretora'),
        ),
    ]
