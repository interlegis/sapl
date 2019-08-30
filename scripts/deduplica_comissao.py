
from sapl.comissoes.models import Comissao, Composicao, Reuniao
from sapl.materia.models import DespachoInicial, Relatoria, UnidadeTramitacao
from sapl.utils import intervalos_tem_intersecao

from difflib import SequenceMatcher

models_dependentes = [Composicao, DespachoInicial, Relatoria, UnidadeTramitacao, Reuniao]

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


def realoca_autor(principal, secundaria):
        autor_principal = principal.autor.first() 
        clone = secundaria.autor.first()

        for autoria in clone.autoria_set.all():
            autoria.autor_id = autor_principal
            autoria.save()
        
        for proposicao in clone.proposicao_set.all():
            proposicao.autor_id = autor_principal
            proposicao.save()
        
        for autorianorma in clone.autorianorma_set.all():
            autorianorma.autor_id = autor_principal
            autorianorma.save()
        
        for documentoadministrativo in clone.documentoadministrativo_set.all():
            documentoadministrativo.autor_id = autor[0]
            documentoadministrativo.save()
        
        for protocolo in clone.protocolo_set.all():
            protocolo.autor_id = autor_principal
            protocolo.save()

            clone.delete()

def redireciona_apaga(principal,secundaria,apaga):
    if(apaga):
        secundaria.delete()
    else:
        secundaria.comissao = principal
        secundaria.save()


def muda_models_dependentes(principal,secundaria):
    for model in models_dependentes:
        for obj_secundario in model.objects.filter(comissao=secundaria):
            for obj_principal in model.objects.filter(comissao=principal):
                apaga = False

                if model == Composicao:
                    apaga = intervalos_tem_intersecao(obj_principal.periodo.data_inicio, 
                                         obj_principal.periodo.data_fim,
                                         obj_secundario.periodo.data_inicio,
                                         obj_secundario.periodo.data_fim)
                
                elif model == DespachoInicial:
                    apaga = obj_principal.materia == obj_secundario.materia
                
                elif model == Reuniao:
                    apaga = obj_principal.numero == obj_secundario.numero
                
                else:
                    apaga = False

                redireciona_apaga(obj_principal, obj_secundario, apaga)

def junta_dulpicados(duplicados):
    principal = duplicados[-1]
    for secundaria in duplicados[:-1]:
        muda_models_dependentes(principal,secundaria)
        realoca_autor(principal, secundaria)
        secundaria.delete()       


def main():
    lst_duplicados = detecta_duplicados()
    print('Duplicados encomtrados:\n')
    print(lst_duplicados)
    for c in lst_duplicados:
        junta_dulpicados(c)

if __name__ == '__main__':
    main()
