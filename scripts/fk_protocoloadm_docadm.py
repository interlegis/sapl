# Esse script foi feito para substituir a referência a Protocolo
# em algum Documento, que antes era numero e ano, para uma FK


from django.core.exceptions import ObjectDoesNotExist

from sapl.protocoloadm.models import DocumentoAdministrativo, Protocolo


def substitui():
    for d in DocumentoAdministrativo.objects.all():
        if d.numero_protocolo:
            try:
                d.protocolo = Protocolo.objects.get(
                    ano=d.ano,
                    numero=d.numero_protocolo)
                d.save()
            except ObjectDoesNotExist:
                return


if __name__ == '__main__':
    substitui()
