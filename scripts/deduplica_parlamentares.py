from django.db.models import Count

from sapl.base.models import Autor
from sapl.comissoes.models import Participacao
from sapl.materia.models import Relatoria, UnidadeTramitacao, Autoria, Proposicao
from sapl.norma.models import AutoriaNorma
from sapl.parlamentares.models import Parlamentar, ComposicaoMesa, Dependente, Filiacao, Mandato, Frente, Votante
from sapl.protocoloadm.models import Protocolo, DocumentoAdministrativo
from sapl.sessao.models import IntegranteMesa, JustificativaAusencia, OradorExpediente, PresencaOrdemDia, \
    RetiradaPauta, SessaoPlenariaPresenca, VotoParlamentar, OradorOrdemDia


models = [ComposicaoMesa, Dependente, Filiacao, IntegranteMesa, JustificativaAusencia, Mandato, OradorOrdemDia,
          OradorExpediente, Participacao, PresencaOrdemDia, Relatoria, RetiradaPauta, SessaoPlenariaPresenca,
          UnidadeTramitacao, VotoParlamentar, Votante]

# Tratar FRENTE pois ela é 1-to-many (campo parlamentares) com Parlamentar

models_autor = [AutoriaNorma, Autoria, Frente, Proposicao, Protocolo, DocumentoAdministrativo]

## Verificar se TipoAutor é sempre 1 para parlamentar e ContentType é sempre 26 para parlamentar.
TIPO_PARLAMENTAR = 1
CONTENT_TYPE_PARLAMENTAR = 26


def recupera_parlamentares():
    return [[parlamentar for parlamentar in Parlamentar.objects.filter(nome_parlamentar=nome_parlamentar).order_by('id')]
            for nome_parlamentar in Parlamentar.objects.values_list('nome_parlamentar', flat=True)
                .annotate(qntd=Count('nome_parlamentar')).filter(qntd__gt=1)]


def deduplica_parlamentares(parlamentares):
    for parlamentar in parlamentares:
        parlamentar_principal = parlamentar[0]
        print('Corrigindo parlamentar {}'.format(parlamentar_principal))
        for clone in parlamentar[1:]:
            if parlamentar_principal.biografia and clone.biografia:
                parlamentar_principal.biografia += f'\n\n------------------------\n\n{clone.biografia}'
                parlamentar_principal.save()
            elif clone.biografia:
                parlamentar_principal.biografia = clone.biografia

            autor_principal = Autor.objects.filter(tipo_id=TIPO_PARLAMENTAR,
                                                   content_type_id=CONTENT_TYPE_PARLAMENTAR,
                                                   object_id=parlamentar_principal.id)

            for a in Autor.objects.filter(tipo_id=TIPO_PARLAMENTAR, content_type_id=CONTENT_TYPE_PARLAMENTAR, object_id=clone.id):
                if not autor_principal:
                    print('Ajustando autor de %s' % parlamentar)
                    a.object_id = parlamentar_principal.id
                    try:
                        a.save()
                    except Exception as e:
                        print(f"Erro ao mover referencia de autor do model {ma} para {autor_principal[0]}")
                        print(e)
                else:
                    print('Movendo referencias de autor')
                    for ma in models_autor:
                        for ra in ma.objects.filter(autor=a):
                            ra.autor = autor_principal[0]
                            try:
                                ra.save()
                            except Exception as e:
                                print(f"Erro ao mover referencia de autor do model {ma} para {autor_principal[0]}")
                                print(e)
                    a.delete()

            # Muda apontamento de models que referenciam parlamentar
            for model in models:
                print(f"Mudando apontamento de model {model}...")
                for obj in model.objects.filter(parlamentar_id=clone.id):
                    obj.parlamentar = parlamentar_principal
                    try:
                        obj.save()
                    except Exception as e:
                        print(f"Erro ao alterar parlamentar do model {model} para a instancia {obj}")
                        print(e)
            clone.delete()


def estatisticas(parlamentares):
    stats = []
    for ps in parlamentares:
        for p in ps:
            d = {
                'id': p.id,
                'nome': p.nome_parlamentar,
                'stats': {m.__name__: m.objects.filter(parlamentar=p).count() for m in models}
            }
            for m in models_autor:
                d['stats'].update({m.__name__:m.objects.filter(autor__object_id=p.id,
                                                               autor__content_type=CONTENT_TYPE_PARLAMENTAR,
                                                               autor__tipo_id=TIPO_PARLAMENTAR).count()})
            stats.append(d)
    for s in stats:
        print('---------------------------------------------------')
        print(s['id'], s['nome'])
        print(s['stats'])


def main():
    parlamentares = recupera_parlamentares()
    estatisticas(parlamentares)
    deduplica_parlamentares(parlamentares)
    estatisticas(parlamentares)


if __name__ == '__main__':
    main()
