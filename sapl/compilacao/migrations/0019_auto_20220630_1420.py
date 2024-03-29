# Generated by Django 2.2.24 on 2022-06-30 17:20

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('compilacao', '0018_auto_20210227_2152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_atualizador',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='dispositivos_alterados_set', to='compilacao.Dispositivo', verbose_name='Dispositivo Atualizador'),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_pai',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dispositivos_filhos_set', to='compilacao.Dispositivo', verbose_name='Dispositivo Pai'),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='dispositivo_raiz',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='nodes', to='compilacao.Dispositivo', verbose_name='Dispositivo Raiz'),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='publicacao',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='compilacao.Publicacao', verbose_name='Publicação'),
        ),
        migrations.AlterField(
            model_name='dispositivo',
            name='ta_publicado',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='dispositivos_alterados_pelo_ta_set', to='compilacao.TextoArticulado', verbose_name='Texto Articulado Publicado'),
        ),
        migrations.AlterField(
            model_name='publicacao',
            name='ta',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='compilacao.TextoArticulado', verbose_name='Texto Articulado'),
        ),
    ]
