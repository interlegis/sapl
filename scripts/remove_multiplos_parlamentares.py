import re

from sapl.base.models import Autor
from sapl.comissoes.models import Participacao
from sapl.materia.models import Relatoria, UnidadeTramitacao
from sapl.parlamentares.models import Parlamentar, ComposicaoMesa, Dependente, Filiacao, Mandato
from sapl.sessao.models import IntegranteMesa, JustificativaAusencia, Orador, OradorExpediente, PresencaOrdemDia, \
    RetiradaPauta, SessaoPlenariaPresenca, VotoParlamentar


def get_multiple(top_models):
    pks_objs = {}

    for model in top_models:
        model_name = re.findall(r'\w+', str(model))[-1]
        pks_objs.update({model_name: []})

        objs = model.objects.all()

        for obj in objs:

            if model_name == 'Autor':
                kwargs = {'nome': obj.nome}
            elif model_name == 'Parlamentar':
                kwargs = {'nome_parlamentar': obj.nome_parlamentar}
            else:
                print('Model não reconhecida.')
                return

            pesquisa_obj = model.objects.filter(**kwargs)
            if pesquisa_obj.count() > 1:
                multiplos_objs = [p.pk for p in pesquisa_obj]
                multiplos_objs.sort()

                if multiplos_objs not in pks_objs.get(model_name):
                    pks_objs.get(model_name).append(multiplos_objs)

    return pks_objs


def transfer_author(pks_list):
    for pks in pks_list:
        for pk in pks[1:]:
            autor_clonado = Autor.objects.get(pk=pk)

            for autoria in autor_clonado.autoria_set.all():
                autoria.autor_id = pks[0]
                autoria.save()

            for proposicao in autor_clonado.proposicao_set.all():
                proposicao.autor_id = pks[0]
                proposicao.save()

            for autorianorma in autor_clonado.autorianorma_set.all():
                autorianorma.autor_id = pks[0]
                autorianorma.save()

            for documentoadministrativo in autor_clonado.documentoadministrativo_set.all():
                documentoadministrativo.autor_id = pks[0]
                documentoadministrativo.save()

            for protocolo in autor_clonado.protocolo_set.all():
                protocolo.autor_id = pks[0]
                protocolo.save()


def transfer_congressman(models, pks_list):
    for pks in pks_list:
        for pk in pks[1:]:
            for model in models:
                for obj in model.objects.filter(parlamentar_id=pk):
                    obj.parlamentar_id = pks[0]
                    obj.save()


def purge(top_models, pks_dict):
    for model in top_models:
        model_name = re.findall(r'\w+', str(model))[-1]

        lista = pks_dict.get(model_name)
        if lista:
            for pks in lista:
                for pk in pks[1:]:
                    for obj in model.objects.filter(pk=pk):
                        obj.delete()


def main():
    top_models = [Autor, Parlamentar]
    models = [ComposicaoMesa, Dependente, Filiacao, IntegranteMesa, JustificativaAusencia, Mandato, Orador,
              OradorExpediente, Participacao, PresencaOrdemDia, Relatoria, RetiradaPauta, SessaoPlenariaPresenca,
              UnidadeTramitacao, VotoParlamentar]

    pks_dict = get_multiple(top_models)

    author_list = pks_dict.get('Autor')
    if author_list:
        transfer_author(author_list)

    congressman_list = pks_dict.get('Parlamentar')
    if congressman_list:
        transfer_congressman(models, congressman_list)

    purge(top_models, pks_dict)


if __name__ == '__main__':
    main()
