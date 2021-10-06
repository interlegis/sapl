# Generated by Django 2.2.24 on 2021-10-06 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0056_sessaoplenaria_status_cronometro'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sessaoplenaria',
            name='status_cronometro',
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='status_cronometro_aparte',
            field=models.CharField(default='S', max_length=1, verbose_name='Status do cronômetro aparte'),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='status_cronometro_consideracoes_finais',
            field=models.CharField(default='S', max_length=1, verbose_name='Status do cronômetro consideracoes finais'),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='status_cronometro_discurso',
            field=models.CharField(default='S', max_length=1, verbose_name='Status do cronômetro discurso'),
        ),
        migrations.AddField(
            model_name='sessaoplenaria',
            name='status_cronometro_ordem_do_dia',
            field=models.CharField(default='S', max_length=1, verbose_name='Status do cronômetro ordem do dia'),
        ),
    ]