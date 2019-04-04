import re

from django.core.exceptions import ObjectDoesNotExist

from sapl.base.models import Autor
from sapl.comissoes.models import Participacao
from sapl.materia.models import Relatoria, UnidadeTramitacao, Autoria
from sapl.parlamentares.models import Parlamentar, ComposicaoMesa, Dependente, Filiacao, Mandato
from sapl.sessao.models import IntegranteMesa, JustificativaAusencia, Orador, OradorExpediente, PresencaOrdemDia, \
    RetiradaPauta, SessaoPlenariaPresenca, VotoParlamentar


def get_multiples():
    models = [Autor, Parlamentar]
    multiples = {}

    for model in models:
        model_name = re.findall(r'\w+', str(model))[-1]
        multiples[model_name] = {
            'kwargs': {},
            'pks': []
        }

        objs = model.objects.all()
        for obj in objs:
            if model_name == 'Autor':
                multiples[model_name]['kwargs']['nome'] = obj.nome
            elif model_name == 'Parlamentar':
                multiples[model_name]['kwargs']['nome_parlamentar'] = obj.nome_parlamentar

            pesquisa_obj = model.objects.filter(**multiples[model_name]['kwargs'])
            if pesquisa_obj.count() > 1:
                multiplos_objs = [o.pk for o in pesquisa_obj]
                multiplos_objs.sort()

                if multiplos_objs not in multiples[model_name]['pks']:
                    multiples[model_name]['pks'].append(multiplos_objs)

        if not multiples[model_name]['pks']:
            multiples.pop(model_name)
        else:
            multiples[model_name].pop('kwargs')

    return multiples


def transfer_purge_author(author_lists):
    for author_list in author_lists:
        for pk in author_list[1:]:
            autor_clonado = Autor.objects.get(pk=pk)

            for autoria in autor_clonado.autoria_set.all():
                autoria.autor_id = author_list[0]
                autoria.save()

            for proposicao in autor_clonado.proposicao_set.all():
                proposicao.autor_id = author_list[0]
                proposicao.save()

            for autorianorma in autor_clonado.autorianorma_set.all():
                autorianorma.autor_id = author_list[0]
                autorianorma.save()

            for documentoadministrativo in autor_clonado.documentoadministrativo_set.all():
                documentoadministrativo.autor_id = author_list[0]
                documentoadministrativo.save()

            for protocolo in autor_clonado.protocolo_set.all():
                protocolo.autor_id = author_list[0]
                protocolo.save()

            autor_clonado.delete()


def transfer_purge_congressman(congressman_lists):
    models = [ComposicaoMesa, Dependente, Filiacao, IntegranteMesa, JustificativaAusencia, Mandato, Orador,
              OradorExpediente, Participacao, PresencaOrdemDia, Relatoria, RetiradaPauta, SessaoPlenariaPresenca,
              UnidadeTramitacao, VotoParlamentar]

    for congressman_list in congressman_lists:
        parlamentar_principal = Parlamentar.objects.get(pk=congressman_list[0])
        for pk in congressman_list[1:]:
            parlamentar_clonado = Parlamentar.objects.get(pk=pk)
            if parlamentar_clonado.biografia:
                parlamentar_principal += f'\n\n------------------------\n\n{parlamentar_clonado.biografia}'

            for model in models:
                for obj in model.objects.filter(parlamentar_id=pk):
                    # TODO: Validar objeto para não repeti-lo no parlamentar principal
                    obj.parlamentar_id = congressman_list[0]
                    obj.save()

            # TODO: Transferir para função de autor
            try:
                autor_principal = Autor.objects.get(parlamentar_set=parlamentar_principal)
                autor_clonado = Autor.objects.get(parlamentar_set=parlamentar_clonado)
                for autoria in Autoria.objects.filter(autor=autor_clonado):
                    autoria.autor = autor_principal
                    autoria.save()
            except ObjectDoesNotExist:
                try:
                    autor_clonado = Autor.objects.get(parlamentar_set=parlamentar_clonado)
                    autor_clonado.parlamentar_set = parlamentar_principal
                except ObjectDoesNotExist:
                    pass

            parlamentar_clonado.delete()


def main():
    multiples = get_multiples()

    if multiples.get('Autor'):
        transfer_purge_author(multiples['Autor']['pks'])

    if multiples.get('Parlamentar'):
        transfer_purge_congressman(multiples['Parlamentar']['pks'])


if __name__ == '__main__':
    main()
