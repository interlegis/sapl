from __future__ import unicode_literals

from django.db import migrations


def deduplica_protocolos(apps, schema_editor):
    from sapl.base.views import protocolos_duplicados

    Protocolo = apps.get_model('protocoloadm', 'Protocolo')

    protocolos = protocolos_duplicados()
    for protocolo in protocolos:
        protocolo_principal = Protocolo.objects.filter(numero=protocolo['numero'], ano=protocolo['ano']).order_by('-id')[0]
        Protocolo.objects.filter(numero=protocolo['numero'], ano=protocolo['ano']).exclude(id=protocolo_principal.id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0021_merge_20190429_1531'),
    ]

    operations = [
        migrations.RunPython(deduplica_protocolos)
    ]
