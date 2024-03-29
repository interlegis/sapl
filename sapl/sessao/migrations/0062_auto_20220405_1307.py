# Generated by Django 2.2.24 on 2022-04-05 16:07

from django.db import migrations

def publicar_pauta_true_sessoes_existentes(apps, schema_editor):
    SessaoPlenaria = apps.get_model('sessao', 'SessaoPlenaria')
    SessaoPlenaria.objects.filter(publicar_pauta=False).update(publicar_pauta=True)

class Migration(migrations.Migration):

    dependencies = [
        ('sessao', '0061_sessaoplenaria_publicar_pauta'),
    ]

    operations = [
        migrations.RunPython(publicar_pauta_true_sessoes_existentes),
    ]
