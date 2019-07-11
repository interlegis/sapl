from __future__ import unicode_literals

from django.db import migrations


def deduplica_protocolos(apps, schema_editor):
    from sapl.base.views import protocolos_duplicados

    Protocolo = apps.get_model('protocoloadm', 'Protocolo')

    protocolos = protocolos_duplicados()
    for protocolo in protocolos:
        protocolos_clones = Protocolo.objects.filter(numero=protocolo[0].numero, ano=protocolo[0].ano).order_by('id')[1:]
        for protocolo_dispensavel in protocolos_clones:
            protocolo_dispensavel.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0021_merge_20190429_1531'),
    ]

    operations = [
        migrations.RunPython(deduplica_protocolos)
    ]
