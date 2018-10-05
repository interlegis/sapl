from sapl.parlamentares.models import Mandato


def popula_campo_data_inicio():
    for m in Mandato.objects.all():
        m.data_inicio_mandato = m.legislatura.data_inicio
        m.save()


if __name__ == '__main__':
    popula_campo_data_inicio()
