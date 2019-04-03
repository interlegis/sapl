import re

from sapl.base.models import Autor
from sapl.comissoes.models import Participacao
from sapl.materia.models import Relatoria, UnidadeTramitacao
from sapl.parlamentares.models import Parlamentar, ComposicaoMesa, Dependente, Filiacao, Mandato
from sapl.sessao.models import IntegranteMesa, JustificativaAusencia, Orador, OradorExpediente, PresencaOrdemDia, \
    RetiradaPauta, SessaoPlenariaPresenca, VotoParlamentar


def get_multiple():
    models = [Autor, Parlamentar]
    main_models = {}

    for model in models:
        model_name = re.findall(r'\w+', str(model))[-1]
        main_models[model_name] = {
            'model': model,
            'kwargs': {},
            'pks': []
        }

        objs = main_models[model_name]['model'].objects.all()
        for obj in objs:
            if model_name == 'Autor':
                main_models[model_name]['kwargs']['nome'] = obj.nome
            elif model_name == 'Parlamentar':
                main_models[model_name]['kwargs']['nome_parlamentar'] = obj.nome_parlamentar

            pesquisa_obj = main_models[model_name]['model'].objects.filter(**main_models[model_name]['kwargs'])
            if pesquisa_obj.count() > 1:
                multiplos_objs = [o.pk for o in pesquisa_obj]
                multiplos_objs.sort()

                if multiplos_objs not in main_models[model_name]['pks']:
                    main_models[model_name]['pks'].append(multiplos_objs)

    return main_models


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


# def transfer_congressman(congressman_lists):
#     models = [ComposicaoMesa, Dependente, Filiacao, IntegranteMesa, JustificativaAusencia, Mandato, Orador,
#               OradorExpediente, Participacao, PresencaOrdemDia, Relatoria, RetiradaPauta, SessaoPlenariaPresenca,
#               UnidadeTramitacao, VotoParlamentar]
#     models_dict = {}
#
#     for model in models:
#         model_str = re.findall('\w+', str(model))[-1]
#         models_dict[model_str] = {
#             'model': model,
#             'objs': []
#         }
#
#     for congressman_list in congressman_lists:
#
#         for pk in congressman_list:
#         for pk in pks[1:]:
#
#             for model in models:
#                 for obj in model.objects.filter(parlamentar_id=pk):
#                     obj.parlamentar_id = pks[0]
#                     obj.save()


# def purge(pks_dict):
#     for model in top_models:
#         model_name = re.findall(r'\w+', str(model))[-1]
#
#         lista = pks_dict.get(model_name)
#         if lista:
#             for pks in lista:
#                 for pk in pks[1:]:
#                     for obj in model.objects.filter(pk=pk):
#                         obj.delete()


def main():
    main_models = get_multiple()

    author_lists = main_models['Autor']['pks']
    if author_lists:
        transfer_purge_author(author_lists)

    import ipdb; ipdb.set_trace()
    # congressman_lists = main_models['Parlamentar']['pks']
    # if congressman_lists:
    #     transfer_congressman(congressman_lists)

    # purge(main_models)


if __name__ == '__main__':
    main()
