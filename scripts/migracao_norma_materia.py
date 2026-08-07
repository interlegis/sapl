import os

import sapl.utils

from sapl import settings
from sapl.norma.models import NormaJuridica, TipoNormaJuridica
from sapl.materia.models import MateriaLegislativa, TipoMateriaLegislativa, RegimeTramitacao
from django.utils import timezone

from sapl.utils import texto_upload_path


def migra_atas_normas(tipos_array):
    for t in tipos_array:
        print(t['old_descricao'])
        for x in NormaJuridica.objects.filter(tipo__descricao__icontains=t['old_descricao']):
            tipo_materia = get_or_create_tipo_materia(t['sigla'], t['descricao'])
            n_mat = create_materia_from_norma(x, tipo_materia)
            if n_mat is not None:
                if NormaJuridica.objects.get(pk=x.id).delete():
                    print("Removida NormaJuridica:", x)
            else:
                print("Impossível copiar Norma para tipo Materia:", x)

    for t in tipos_array:
        a = TipoNormaJuridica.objects.filter(descricao__icontains=t['old_descricao']).first()
        print(a, t['old_descricao'])
        if a is not None:
            print("Removido TipoNormaJuridica:", a)
            a.delete()
        else:
            print("Erro ao remover TipoNormaJuridica:", a)


def get_or_create_tipo_materia(sigla, descricao):
    tipo_materia = TipoMateriaLegislativa.objects.filter(descricao=descricao, sigla=sigla).first()

    if not tipo_materia:
        tipo_materia = TipoMateriaLegislativa(sigla=sigla, descricao=descricao)
        tipo_materia.save()

    return tipo_materia


def create_materia_from_norma(norma, tipo):
    if not norma or not tipo:
        print("Norma e/ou tipo invalidos:", norma, tipo)
        return False
    else:
        n_materia = MateriaLegislativa()
        n_materia.tipo = tipo
        if norma.numero:
            n_materia.numero = norma.numero
        if norma.ano:
            n_materia.ano = norma.ano
        if norma.data_publicacao:
            n_materia.data_publicacao = norma.data_publicacao
        if norma.ementa:
            n_materia.ementa = norma.ementa
        if norma.texto_integral:
            n_materia.texto_original = norma.texto_integral
        if norma.data_ultima_atualizacao:
            n_materia.data_ultima_atualizacao = norma.data_ultima_atualizacao
        if norma.user:
            n_materia.user = norma.user
        if norma.ip:
            n_materia.ip = norma.ip
        if norma.ultima_edicao:
            n_materia.ultima_edicao = norma.ultima_edicao
        if norma.data is None:
            n_materia.data_apresentacao = timezone.now()
        else:
            n_materia.data_apresentacao = norma.data
        n_materia.regime_tramitacao = RegimeTramitacao.objects.first()

        n_materia.save()
        print("Criada nova MateriaLegislativa:", n_materia.__str__())
        update_file_location_to_new_model(n_materia)
    return True


def update_file_location_to_new_model(new_model):
    try:
        initial_path = new_model.texto_original.path
    except ValueError:
        print("arquivo não existe", new_model.texto_original.name)
        return False

    if not os.path.exists(initial_path):
        print("Arquivo nao existe:", initial_path)
        return False

    # get new path using already defined function
    print(os.path.basename(new_model.texto_original.name))
    new_name = texto_upload_path(new_model, os.path.basename(new_model.texto_original.name), subpath=new_model.ano)
    new_path = os.path.join(settings.MEDIA_ROOT, new_name)
    print("New name:", new_name)
    print("Novo diretorio:", new_path)
    # check if the dir exists
    if not os.path.exists(os.path.dirname(new_path)):
        print("criando novo diretorio...:", os.path.dirname(new_path))
        os.makedirs(os.path.dirname(new_path))

    if os.path.exists(os.path.dirname(new_path)):
        print("movendo arquivo de local:", new_path)
        os.rename(initial_path, new_path)
        # Update the file field
        new_model.texto_original.name = new_name
        new_model.save()
        print("success!", new_model.texto_original)
        return True
    else:
        print("Não foi possível criar diretorio:", os.path.dirname(new_path))

    return False


def main():
    tipos_movimentacao = [
        {
            'old_descricao': 'ATA COMISS',
            'descricao': 'Ata de Comissão',
            'sigla': 'ACM'
        },
        {
            'old_descricao': 'ATA CPI Nº 01',
            'descricao': 'Ata CPI',
            'sigla': 'ACPI'
        },
        {
            'old_descricao': 'Atas Audiências Públicas',
            'descricao': 'Ata de Audiência Pública',
            'sigla': 'AAP'
        },
        {
            'old_descricao': 'ATAS DA CPI Nº 2',
            'descricao': 'Ata de CPI',
            'sigla': 'ACPI'
        },
        {
            'old_descricao': 'Atas Reuniões Extraordinárias',
            'descricao': 'Ata de Reunião Extraordinária',
            'sigla': 'ARE'
        },
        {
            'old_descricao': 'Atas Reuniões Ordinárias',
            'descricao': 'Ata de Reunião Ordinária',
            'sigla': 'ARO'
        },
    ]
    migra_atas_normas(tipos_movimentacao)


if __name__ == '__main__':
    main()
