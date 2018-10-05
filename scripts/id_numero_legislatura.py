from sapl.parlamentares.models import Legislatura


def popula_numero_legislatura_id():
    for l in Legislatura.objects.all():
        l.numero = l.id
        l.save()


if __name__ == '__main__':
    popula_numero_legislatura_id()
