# Generated by Django 2.2.13 on 2020-10-05 13:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('parlamentares', '0032_frente_parlamentar'),
    ]

    operations = [
        migrations.CreateModel(
            name='BlocoCargo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_cargo', models.CharField(max_length=120, verbose_name='Cargo do bloco parlamentar')),
                ('cargo_unico', models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')], default=False, verbose_name='Cargo único?')),
            ],
            options={
                'verbose_name': 'Cargo de Bloco Parlamentar',
                'verbose_name_plural': 'Cargos de Bloco Parlamentar',
                'ordering': ('cargo_unico', 'nome_cargo'),
            },
        ),
        migrations.AlterModelOptions(
            name='bloco',
            options={'ordering': ('partidos__nome', 'nome'), 'verbose_name': 'Bloco Parlamentar', 'verbose_name_plural': 'Blocos Parlamentares'},
        ),
        migrations.AlterField(
            model_name='bloco',
            name='nome',
            field=models.CharField(max_length=120, verbose_name='Nome do Bloco'),
        ),
        migrations.CreateModel(
            name='BlocoMembro',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_entrada', models.DateField(verbose_name='Data Entrada')),
                ('data_saida', models.DateField(blank=True, null=True, verbose_name='Data Saída')),
                ('bloco', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parlamentares.Bloco', verbose_name='Bloco parlamentar')),
                ('cargo', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='parlamentares.BlocoCargo', verbose_name='Cargo na bloco parlamentar')),
                ('parlamentar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='parlamentares.Parlamentar', verbose_name='Parlamentar')),
            ],
            options={
                'verbose_name': 'Membro de bloco parlamentar',
                'verbose_name_plural': 'Membros de bloco parlamentar',
                'ordering': ('bloco', 'parlamentar', 'cargo'),
            },
        ),
    ]
