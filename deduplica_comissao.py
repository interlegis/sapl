from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Count

from sapl.base.models import TipoAutor, Autor
from sapl.comissoes.models import Composicao, Comissao, Reuniao
from sapl.materia.models import DespachoInicial, Autoria, Proposicao, Relatoria, UnidadeTramitacao, Tramitacao, \
    MateriaLegislativa
from sapl.norma.models import AutoriaNorma
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo, TramitacaoAdministrativo

models_comissoes = [Composicao, DespachoInicial, Relatoria, Reuniao]

models_autor = [Autoria, AutoriaNorma, Proposicao, Protocolo, DocumentoAdministrativo]


def move_comissao(from_id, to_id):
    # TODO: verificar se content type é o mesmo para todos os BD
    content_type = ContentType.objects.get(id=37)
    tipo = TipoAutor.objects.get(id=2)

    _from_comissao = Comissao.objects.get(id=from_id)
    _to_comissao = Comissao.objects.get(id=to_id)

    ## TRATA TRAMITACAO
    try:
        _to_unidade_tramitacao = UnidadeTramitacao.objects.get_or_create(comissao=_to_comissao)
    except ObjectDoesNotExist:
        _to_unidade_tramitacao = UnidadeTramitacao.objects.create(comissao=_to_comissao)

    models_tramitacao = [Tramitacao, TramitacaoAdministrativo]

    for m in models_tramitacao:
        for t1 in m.objects.filter(unidade_tramitacao_local__comissao=_from_comissao):
            t1.unidade_tramitacao_local = _to_unidade_tramitacao
            t1.save()

        for t1 in m.objects.filter(unidade_tramitacao_destino__comissao=_from_comissao):
            t1.unidade_tramitacao_destino = _to_unidade_tramitacao
            t1.save()

    UnidadeTramitacao.objects.filter(comissao=_from_comissao).delete()

    for m in models_comissoes:
        print('atualizando model {}'.format(m))
        objects = m.objects.filter(comissao=_from_comissao)
        for o in objects:
            try:
                o.comissao = _to_comissao
                o.save()
            except IntegrityError as e:
                print(str(e))
                o.delete()



    autor_from = Autor.objects.filter(content_type=content_type,
                                      tipo=tipo,
                                      object_id=_from_comissao.id).values_list('id')
    if not autor_from:
        return

    try:
        autor_to = Autor.objects.get(content_type=content_type,
                                     tipo=tipo,
                                     object_id=_to_comissao.id)
    except ObjectDoesNotExist:
        print('criando autor para {}-{}'.format(_to_comissao.id, _to_comissao.nome))
        autor_to = Autor.objects.create(nome=_to_comissao.nome,
                                        tipo=tipo,
                                        content_type=content_type,
                                        object_id=_to_comissao.id)

    to_delete = []

    for m in models_autor:
        print('atualizando autoria para {}'.format(m))
        objects = m.objects.filter(autor_id__in=autor_from)
        for o in objects:
            try:
                original_autor = o.autor
                o.autor = autor_to
                o.save()
            except IntegrityError as e:
                o.autor = original_autor
                o.save()
                to_delete.append(o)

    for d in to_delete:
        d.delete()

    # REMOVE AUTORES DUPLICADOS
    Autor.objects.filter(id__in=autor_from).delete()


def estatisticas():
    # TODO: verificar se content type é o mesmo para todos os BD
    content_type = ContentType.objects.get(id=37)
    tipo = TipoAutor.objects.get(id=2)

    for c in Comissao.objects.all().order_by('nome'):
        print('-------------------------------------------------------------------')
        print(c)

        for m in models_comissoes + [UnidadeTramitacao]:
            model_name = m.__name__
            total = m.objects.filter(comissao=c).count()
            print(model_name, total)

        try:
            autor = Autor.objects.get(content_type=content_type, tipo=tipo, object_id=c.id)
            for a in models_autor:
                model_name = a.__name__
                total = a.objects.filter(autor=autor).count()
                print(model_name, total)
        except Exception as e:
            print(str(e))
            pass
        print('-------------------------------------------------------------------')


def delete_comissao(id):
    # TODO: verificar se content type é o mesmo para todos os BD
    content_type = ContentType.objects.get(id=37)
    tipo = TipoAutor.objects.get(id=2)
    comissao = Comissao.objects.get(id=id)

    for m in models_comissoes:
        m.objects.filter(comissao=comissao).delete()

    try:
        autor = Autor.objects.get(content_type=content_type, tipo=tipo, object_id=comissao.id)
        for a in models_autor:
            a.objects.filter(autor=autor).delete()
        autor.delete()
    except Exception as e:
        print(str(e))

    try:
        unidate_tramitacao = UnidadeTramitacao.objects.get(comissao=comissao)
        models_tramitacao = [Tramitacao, TramitacaoAdministrativo]
        for m in models_tramitacao:
            m.objects.filter(unidade_tramitacao_local=unidate_tramitacao).delete()
            m.objects.filter(unidade_tramitacao_destino=unidate_tramitacao).delete()
        unidate_tramitacao.delete()
    except Exception as e:
        print(str(e))

    comissao.delete()


def deduplicate_comissao():
    # TODO: verificar se content type é o mesmo para todos os BD
    content_type = ContentType.objects.get(id=37)
    tipo = TipoAutor.objects.get(id=2)
    comissoes_repetidas = [(c['nome'], c['total']) for c in
                           Comissao.objects.values('nome').annotate(total=Count('nome')).filter(total__gt=1)]
    print(comissoes_repetidas)
    for cr in comissoes_repetidas:
        comissoes = list(Comissao.objects.filter(nome=cr[0]).order_by('id').values_list('id', flat=True))

        print(cr)
        print(comissoes)

        ## TODO: PODEM EXISTIR CASOS DA COMISSAO DE DESTINO NAO TER AUTOR, TERIA QUE CRIAR
        ## TODO: POR ENQUANTO OPTEI POR PEGAR A ULTIMA COMISSAO COM AUTOR CRIADO
        while True:
            c = comissoes.pop(0)
            try:
                Autor.objects.get(content_type=content_type, tipo=tipo, object_id=c)
                comissoes = [c] + comissoes
                break
            except ObjectDoesNotExist:
                comissoes.append(c)

        print(comissoes)

        principal = comissoes[0]
        repetidas = comissoes[1:]

        for r in repetidas:
            move_comissao(r, principal)
            print('apagando comissao {}'.format(r))
            Comissao.objects.get(id=r).delete()

estatisticas()
deduplicate_comissao()
estatisticas()




