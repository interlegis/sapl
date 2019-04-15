from sapl.materia.models import MateriaLegislativa
from sapl.protocoloadm.models import Protocolo


def main():
    for materia in MateriaLegislativa.objects.filter(numero_protocolo__isnull=False):
        if not Protocolo.objects.filter(ano=materia.ano, numero=materia.numero_protocolo).exists():
            materia.numero_protocolo = None
            materia.save()


if __name__ == '__main__':
    main()
