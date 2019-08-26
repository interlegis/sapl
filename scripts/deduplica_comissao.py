
from sapl.comissoes.models import Comissao, Composicao
from sapl.materia.models import DespachoInicial, Relatoria, UnidadeTramitacao

from difflib import SequenceMatcher

models_dependentes = [Composicao, DespachoInicial, Relatoria, UnidadeTramitacao]

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def detecta_duplicados():
    lst_duplicados = []
    comissoes = Comissao.objects.all().order_by('id')
    for c_1 in comissoes:
        c_1_lst = []
        for c_2 in comissoes:
            if similar(c_1.nome,c_2.nome) > 0.9 and c_1.id != c_2.id:
                c_1_lst.append(c_2)
                comissoes = comissoes.exclude(id=c_2.id)
        if c_1_lst:
            c_1_lst.append(c_1)
            comissoes = comissoes.exclude(id=c_1.id)
            lst_duplicados.append(c_1_lst)
    return lst_duplicados

def junta_dulpicados(duplicados):
    principal = duplicados[-1]
    for c in duplicados[:-1]:
        for m in models_dependentes:
            for obj in m.objects.filter(comissao=c):
                obj.comissao = principal
                obj.save()
        c.delete()       


def main():
    lst_duplicados = detecta_duplicados()
    for c in lst_duplicados:
        junta_dulpicados(c)

if __name__ == '__main__':
    main()
