from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count
from sapl.base.models import Autor
from sapl.parlamentares.models import Parlamentar


def pega_autores():
    return [[autor for autor in Autor.objects.filter(nome=nome)]
            for nome in Autor.objects.values_list('nome', flat=True).annotate(qntd=Count('nome')).filter(qntd__gt=1)]


def pega_parlamentares_autores():
    parlamentares = [[parlamentar for parlamentar in Parlamentar.objects.filter(nome_parlamentar=nome_parlamentar)]
                     for nome_parlamentar in Parlamentar.objects.values_list('nome_parlamentar', flat=True)
                     .annotate(qntd=Count('nome_parlamentar')).filter(qntd__gt=1)]

    parlamentares_autores = []

    for parlamentar in parlamentares:
        parlamentar_autor = []
        for clone in parlamentar[1:]:
            try:
                autor_principal = Autor.objects.get(parlamentar_set=parlamentar[0])
            except ObjectDoesNotExist:
                try:
                    autor_clonado = Autor.objects.get(parlamentar_set=clone)
                except ObjectDoesNotExist:
                    pass
                else:
                    autor_clonado.object_id = parlamentar[0].id
                    autor_clonado.save()
                    parlamentares_autores.append(autor_clonado)
            else:
                if len(parlamentar_autor) == 0:
                    parlamentar_autor.append(autor_principal)

                try:
                    autor_clonado = Autor.objects.get(parlamentar_set=clone)
                except ObjectDoesNotExist:
                    pass
                else:
                    parlamentar_autor.append(autor_clonado)
        parlamentares_autores.extend(parlamentar_autor)

    return parlamentares_autores


def transfere_valeres(autores):
    for autor in autores:
        for clone in autor[1:]:
            for autoria in clone.autoria_set.all():
                autoria.autor_id = autor[0]
                autoria.save()

            for proposicao in clone.proposicao_set.all():
                proposicao.autor_id = autor[0]
                proposicao.save()

            for autorianorma in clone.autorianorma_set.all():
                autorianorma.autor_id = autor[0]
                autorianorma.save()

            for documentoadministrativo in clone.documentoadministrativo_set.all():
                documentoadministrativo.autor_id = autor[0]
                documentoadministrativo.save()

            for protocolo in clone.protocolo_set.all():
                protocolo.autor_id = autor[0]
                protocolo.save()

            clone.delete()


def main():
    autores = pega_autores()
    parlamentares_autores = pega_parlamentares_autores()

    autores.append(parlamentares_autores)

    transfere_valeres(autores)


if __name__ == '__main__':
    main()
