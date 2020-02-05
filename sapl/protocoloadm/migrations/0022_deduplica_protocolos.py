from __future__ import unicode_literals

from django.db import migrations


def deduplica_protocolos(apps, schema_editor):
    from sapl.base.views import protocolos_duplicados

    Protocolo = apps.get_model('protocoloadm', 'Protocolo')
    DocumentoAdministrativo = apps.get_model('protocoloadm', 'DocumentoAdministrativo')

    protocolos = protocolos_duplicados()
    for p in protocolos:
        principal = Protocolo.objects.filter(numero=p['numero'], ano=p['ano']).order_by('-id').first()
        replicas = Protocolo.objects.filter(numero=p['numero'], ano=p['ano']).exclude(id=principal.id)

        for r in replicas:
            documentos = DocumentoAdministrativo.objects.filter(protocolo_id=r.id)
            for d in documentos:
                d.protocolo = principal
                d.save()
        replicas.delete()

class Migration(migrations.Migration):

    dependencies = [
        ('protocoloadm', '0021_merge_20190429_1531'),
    ]

    operations = [
        migrations.RunPython(deduplica_protocolos)
    ]
