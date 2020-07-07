# Gerar hash de proposições para recebimento sem recibo
from sapl.materia.models import Proposicao
from sapl.utils import gerar_hash_arquivo, SEPARADOR_HASH_PROPOSICAO
from datetime import datetime

def gerar_hash(proposicao):
    if proposicao.texto_original:
        try:
            proposicao.hash_code = gerar_hash_arquivo(
                proposicao.texto_original.path, str(proposicao.pk))
        except IOError:
            raise Exception("Existem proposicoes com arquivos inexistentes.")
    elif proposicao.texto_articulado.exists():
        ta = proposicao.texto_articulado.first()
        proposicao.hash_code = 'P' + ta.hash() + SEPARADOR_HASH_PROPOSICAO + str(proposicao.pk)
        print(proposicao.hash_code)
    proposicao.save()


def gerar_hash_proposicoes():
    di = datetime.now()
    print(di)
    props = Proposicao.objects.filter(hash_code='').exclude(data_envio__isnull=True)
    print("Total de proposicoes: %s" % props.count())
    for prop in props:
        try:
            print(".",end="")
            gerar_hash(prop)
        except Exception as e:
            print('Erro para proposicao', prop)
            print(e)
    
    elapsed = datetime.now() - di
    print("\n {}s".format(elapsed.seconds))

