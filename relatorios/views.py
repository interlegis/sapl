from datetime import datetime

from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.utils.translation import ugettext_lazy as _

from base.models import ESTADOS
from base.models import CasaLegislativa
from comissoes.models import Comissao
from materia.models import (Autor, Autoria, MateriaLegislativa, Numeracao,
                            Tramitacao, UnidadeTramitacao)
from parlamentares.models import (CargoMesa, ComposicaoMesa, Filiacao,
                                  Parlamentar)
from protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                 TramitacaoAdministrativo)
from sessao.models import (ExpedienteMateria, ExpedienteSessao, Orador,
                           OradorExpediente, OrdemDia, PresencaOrdemDia,
                           RegistroVotacao, SessaoPlenaria,
                           SessaoPlenariaPresenca, TipoExpediente)

from .templates import (pdf_capa_processo_gerar,
                        pdf_documento_administrativo_gerar, pdf_espelho_gerar,
                        pdf_etiqueta_protocolo_gerar, pdf_materia_gerar,
                        pdf_ordem_dia_gerar, pdf_pauta_sessao_gerar,
                        pdf_protocolo_gerar, pdf_sessao_plenaria_gerar)


def get_kwargs_params(request, fields):
    kwargs = {}
    for i in fields:
        if '__icontains' in i:
            x = i[:-11]  # remove '__icontains'
        else:
            x = i
        if x in request.GET:
            kwargs[i] = request.GET[x]
    return kwargs


def get_cabecalho(casa):

    cabecalho = {}
    cabecalho["nom_casa"] = casa.nome
    # FIXME i18n
    cabecalho["nom_estado"] = "Estado de " + ESTADOS[casa.uf.upper()]
    return cabecalho


def get_imagem(casa):

    if casa.logotipo:
        return casa.logotipo.path
    else:
        # TODO: recuperar de uma variavel de sistema
        return 'static/img/brasao_transp.gif'


def get_rodape(casa):

    if len(casa.cep) == 8:
        cep = casa.cep[:4] + "-" + casa.cep[5:]
    else:
        cep = ""

    linha1 = casa.endereco

    if cep:
        if casa.endereco:
            linha1 = linha1 + " - "
        linha1 = linha1 + "CEP " + cep

    # substituindo nom_localidade por municipio e sgl_uf por uf
    if casa.municipio:
        linha1 = linha1 + " - " + casa.municipio + " " + casa.uf

    if casa.telefone:
        linha1 = linha1 + _(" Tel.: ") + casa.telefone

    if casa.endereco_web:
        linha2 = casa.endereco_web
    else:
        linha2 = ""

    if casa.email:
        if casa.endereco_web:
            linha2 = linha2 + " - "
        linha2 = linha2 + _("E-mail: ") + casa.email

    data_emissao = datetime.today().strftime("%d/%m/%Y")

    return [linha1, linha2, data_emissao]


def get_materias(mats):

    materias = []
    for materia in mats:
        dic = {}
        dic['titulo'] = materia.tipo.sigla + " " + materia.tipo.descricao \
            + " " + str(materia.numero) + "/" + str(materia.ano)
        dic['txt_ementa'] = materia.ementa

        autores = Autoria.objects.filter(materia=materia)
        dic['nom_autor'] = " "
        for autoria in autores:
            if autoria.autor.parlamentar:
                dic['nom_autor'] = autoria.autor.parlamentar.nome_completo
            elif autoria.autor.comissao:
                dic['nom_autor'] = autoria.autor.comissao.nome

        des_status = ''
        txt_tramitacao = ''

        dic['localizacao_atual'] = " "

        tramitacoes = Tramitacao.objects.filter(
            unidade_tramitacao_destino__isnull=True).order_by(
            'data_tramitacao')

        for tramitacao in tramitacoes:
            des_status = tramitacao.status.descricao
            txt_tramitacao = tramitacao.texto

        # for tramitacao in context.zsql
        #    .tramitacao_obter_zsql(cod_materia
        #        =materia.cod_materia,ind_ult_tramitacao=1):
        #     if tramitacao.cod_unid_tram_dest:
        #         cod_unid_tram = tramitacao.cod_unid_tram_dest
        #     else:
        #         cod_unid_tram = tramitacao.cod_unid_tram_local
        #     for unidade_tramitacao in
        #         context.zsql
        #              .unidade_tramitacao_obter_zsql(
        #                   cod_unid_tramitacao = cod_unid_tram):
        #         if unidade_tramitacao.cod_orgao:
        #             dic['localizacao_atual']=unidade_tramitacao.nom_orgao
        #         else:
        #             dic['localizacao_atual']=unidade_tramitacao.nom_comissao
        #     des_status=tramitacao.des_status
        #     txt_tramitacao=tramitacao.txt_tramitacao

        dic['des_situacao'] = des_status
        dic['ultima_acao'] = txt_tramitacao

        dic['norma_vinculada'] = " "
        # for norma_vinculada in context.zsql
        #     .materia_buscar_norma_juridica_zsql(cod_materia=materia.cod_materia):
        #     dic['norma_vinculada']=
        #       norma_vinculada.des_norma+" "
        #       +str(norma_vinculada.num_norma)+"/"+str(norma_vinculada.ano_norma)

        materias.append(dic)

    return materias


def relatorio_materia(request):
    '''
        pdf_materia_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="relatorio_materia.pdf"'

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    kwargs = get_kwargs_params(request, ['numero',
                                         'ano',
                                         'autor',
                                         'tipo_autor',
                                         'relator',
                                         'interessado__icontains'
                                         ])

    mats = MateriaLegislativa.objects.filter(**kwargs)

    materias = get_materias(mats)

    pdf = pdf_materia_gerar.principal(imagem,
                                      materias,
                                      cabecalho,
                                      rodape)

    response.write(pdf)

    return response


def get_capa_processo(prot):
    protocolos = []
    for p in prot:
        dic = {}
        dic['numero'] = str(p.numero)
        dic['ano'] = str(p.ano)
        dic['data'] = str(p.data) + ' - ' + str(p.hora)
        dic['txt_assunto'] = p.assunto_ementa
        dic['txt_interessado'] = p.interessado
        dic['nom_autor'] = " "
        dic['titulo'] = " "

        if p.autor is not None:
            for autor in Autor.objects.filter(id=p.autor.id):
                if autor.tipo == 'Parlamentar':
                    for parlamentar in Parlamentar.objects.filter(
                            id=p.autor.parlamentar.id):
                        dic['nom_autor'] = parlamentar.nome_completo or ' '
                elif autor.tipo == 'Comissao':
                    for comissao in Comissao.objects.filter(
                            id=p.autor.comissao.id):
                        dic['nom_autor'] = comissao.nome or ' '
                else:
                    dic['nom_autor'] = autor.nome or ' '
        else:
            dic['nom_autor'] = p.interessado

        dic['natureza'] = ''
        if p.tipo_processo == 0:
            dic['natureza'] = 'Administrativo'
        if p.tipo_processo == 1:
            dic['natureza'] = 'Legislativo'

        dic['ident_processo'] = str(p.tipo_materia) or str(p.tipo_documento)

        dic['sgl_processo'] = str(p.tipo_materia) or str(p.tipo_documento)

        dic['num_materia'] = ''
        for materia in MateriaLegislativa.objects.filter(
                numero_protocolo=p.numero, ano=p.ano):
            dic['num_materia'] = str(materia.numero) + '/' + str(materia.ano)

        dic['num_documento'] = ''
        for documento in DocumentoAdministrativo.objects.filter(
                numero=p.numero):
            dic['num_documento'] = str(
                documento.numero) + '/' + str(documento.ano)

        dic['num_processo'] = dic['num_materia'] or dic['num_documento']

        dic['numeracao'] = ''
        for materia_num in MateriaLegislativa.objects.filter(
                numero_protocolo=p.numero, ano=p.ano):
            for numera in Numeracao.objects.filter(materia=materia_num):
                # FIXME i18n
                dic['numeracao'] = 'PROCESSO N&#176; ' + \
                    str(numera.numero) + '/' + str(numera.ano)
        dic['anulado'] = ''
        if p.anulado == 1:
            dic['anulado'] = 'Nulo'

        protocolos.append(dic)
    return protocolos


def relatorio_capa_processo(request):
    '''
        pdf_capa_processo_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_processo.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    kwargs = get_kwargs_params(request, ['numero',
                                         'ano',
                                         'tipo_protocolo',
                                         'tipo_processo',
                                         'assunto__icontains',
                                         # 'interessado__icontains'
                                         ])
    protocolos = Protocolo.objects.filter(**kwargs)
    protocolos_pdf = get_capa_processo(protocolos)
    pdf = pdf_capa_processo_gerar.principal(imagem,
                                            protocolos_pdf,
                                            cabecalho,
                                            rodape)

    response.write(pdf)

    return response


def get_ordem_dia(ordem, sessao):

    # TODO: fazer implementação de ordem dia
    pass


def relatorio_ordem_dia(request):
    '''
        pdf_ordem_dia_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')

    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_ordem_dia.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    kwargs = get_kwargs_params(request, ['numero_ordem'])

    ordem = OrdemDia.objects.filter(**kwargs)

    sessao = SessaoPlenaria.objects.first()
    ordem_pdf = get_ordem_dia(ordem, sessao)

    pdf = pdf_ordem_dia_gerar.principal(imagem,
                                        ordem_pdf,
                                        cabecalho,
                                        rodape)

    response.write(pdf)

    return response


def relatorio_documento_administrativo(request):
    '''
        pdf_documento_administrativo_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_documento_administrativo.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    docs = DocumentoAdministrativo.objects.all()[:50]
    doc_pdf = get_documento_administrativo(docs)

    pdf = pdf_documento_administrativo_gerar.principal(
        imagem,
        doc_pdf,
        cabecalho,
        rodape)
    response.write(pdf)

    return response


def get_documento_administrativo(docs):

    documentos = []
    for d in docs:
        dic = {}
        dic['titulo'] = str(d)
        dic['txt_assunto'] = d.assunto
        dic['txt_interessado'] = d.interessado

        des_status = ''
        txt_tramitacao = ''

        dic['localizacao_atual'] = ' '
        # Será removido o 'última'?
        for t in TramitacaoAdministrativo.objects.filter(
                documento=d, ultima=True):
            if t.unidade_tramitacao_destino:
                cod_unid_tram = t.unidade_tramitacao_destino
            else:
                cod_unid_tram = t.unidade_tramitacao_destino

            for unidade_tramitacao in UnidadeTramitacao.objects.filter(
                    id=cod_unid_tram):
                if unidade_tramitacao.orgao:
                    dic['localizacao_atual'] = unidade_tramitacao.orgao
                else:
                    dic['localizacao_atual'] = unidade_tramitacao.comissao

            des_status = t.status.descricao
            txt_tramitacao = t.texto

        dic['des_situacao'] = des_status
        dic['ultima_acao'] = txt_tramitacao

        documentos.append(dic)
    return documentos


def relatorio_espelho(request):
    '''
        pdf_espelho_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = 'attachment; filename="relatorio_espelho.pdf"'

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    mats = MateriaLegislativa.objects.all()[:50]
    mat_pdf = get_espelho(mats)

    pdf = pdf_espelho_gerar.principal(
        imagem,
        mat_pdf,
        cabecalho,
        rodape)
    response.write(pdf)

    return response


def get_espelho(mats):
    materias = []
    for m in mats:
        dic = {}
        dic['titulo'] = str(m)
        dic['materia'] = str(m.numero) + '/' + str(m.ano)
        dic['dat_apresentacao'] = str(m.data_apresentacao)
        dic['txt_ementa'] = m.ementa

        dic['nom_autor'] = ' '
        for autoria in Autoria.objects.filter(materia=m, primeiro_autor=True):
            for autor in Autor.objects.filter(id=autoria.autor.id):
                if autor.tipo == 'Parlamentar':
                    for parlamentar in Parlamentar.objects.filter(
                            id=autor.parlamentar.id):
                        dic['nom_autor'] = parlamentar.nome_completo
                elif autor.tipo == 'Comissao':
                    for comissao in Comissao.objects.filter(
                            id=autor.comissao.id):
                        dic['nom_autor'] = str(comissao)
                else:
                    dic['nom_autor'] = autor.nome

        des_status = ''
        txt_tramitacao = ''
        data_ultima_acao = ''

        dic['localizacao_atual'] = " "
        for tramitacao in Tramitacao.objects.filter(materia=m):
            if tramitacao.unidade_tramitacao_destino:
                cod_unid_tram = tramitacao.unidade_tramitacao_destino
            else:
                cod_unid_tram = tramitacao.unidade_tramitacao_local

            for unidade_tramitacao in UnidadeTramitacao.objects.filter(
                    id=cod_unid_tram.id):
                if unidade_tramitacao.orgao:
                    dic['localizacao_atual'] = unidade_tramitacao.orgao
                elif unidade_tramitacao.parlamentar:
                    dic['localizacao_atual'] = unidade_tramitacao.parlamentar
                else:
                    dic['localizacao_atual'] = unidade_tramitacao.comissao

            des_status = tramitacao.status
            txt_tramitacao = tramitacao.texto
            data_ultima_acao = tramitacao.data_tramitacao

        dic['des_situacao'] = des_status
        dic['ultima_acao'] = txt_tramitacao
        dic['data_ultima_acao'] = data_ultima_acao

        dic['norma_juridica_vinculada'] = _('Não há nenhuma \
                                           norma jurídica vinculada')
        # TODO
        # for norma in context.zsql.materia_buscar_norma_juridica_zsql(
        #       cod_materia=materia.cod_materia):
        #     dic['norma_juridica_vinculada'] = norma.des_norma + " " + \
        #         str(norma.num_norma) + "/" + str(norma.ano_norma)

        materias.append(dic)
    return materias


def get_sessao_plenaria(sessao, casa):

    inf_basicas_dic = {}
    inf_basicas_dic["num_sessao_plen"] = str(sessao.numero)
    inf_basicas_dic["nom_sessao"] = sessao.tipo.nome
    inf_basicas_dic["num_legislatura"] = str(sessao.legislatura)
    inf_basicas_dic["num_sessao_leg"] = sessao.sessao_legislativa.numero
    inf_basicas_dic["dat_inicio_sessao"] = sessao.data_inicio.strftime(
        "%d/%m/%Y")
    inf_basicas_dic["hr_inicio_sessao"] = sessao.hora_inicio
    inf_basicas_dic["dat_fim_sessao"] = sessao.data_fim.strftime("%d/%m/%Y")
    inf_basicas_dic["hr_fim_sessao"] = sessao.hora_fim
    inf_basicas_dic["nom_camara"] = casa.nome

    # Lista da composicao da mesa diretora
    lst_mesa = []
    for composicao in ComposicaoMesa.objects.filter(
            sessao_legislativa=sessao.sessao_legislativa):
        for parlamentar in Parlamentar.objects.filter(
                id=composicao.parlamentar.id):
            for cargo in CargoMesa.objects.filter(id=composicao.cargo.id):
                dic_mesa = {}
                dic_mesa['nom_parlamentar'] = parlamentar.nome_parlamentar
                dic_mesa['sgl_partido'] = Filiacao.objects.filter(
                    parlamentar=parlamentar).first().partido.sigla
                dic_mesa['des_cargo'] = cargo.descricao
                lst_mesa.append(dic_mesa)

    # Lista de presença na sessão
    lst_presenca_sessao = []
    for presenca in SessaoPlenariaPresenca.objects.filter(
            sessao_plenaria=sessao):
        for parlamentar in Parlamentar.objects.filter(
                id=presenca.parlamentar.id):
            dic_presenca = {}
            dic_presenca["nom_parlamentar"] = parlamentar.nome_parlamentar
            dic_presenca['sgl_partido'] = Filiacao.objects.filter(
                parlamentar=parlamentar).first().partido.sigla
            lst_presenca_sessao.append(dic_presenca)

    # Exibe os Expedientes
    lst_expedientes = []
    for tip_expediente in TipoExpediente.objects.all():
        for expediente in ExpedienteSessao.objects.filter(
                sessao_plenaria=sessao, tipo=tip_expediente):
            dic_expedientes = {}
            dic_expedientes["nom_expediente"] = str(tip_expediente)
            dic_expedientes["txt_expediente"] = (
                BeautifulSoup(expediente.conteudo).text)
        if dic_expedientes:
            lst_expedientes.append(dic_expedientes)

    # Lista das matérias do Expediente, incluindo o resultado das votacoes
    lst_expediente_materia = []
    for expediente_materia in ExpedienteMateria.objects.filter(
            sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = MateriaLegislativa.objects.filter(
            id=expediente_materia.materia.id).first()

        dic_expediente_materia = {}
        dic_expediente_materia["num_ordem"] = expediente_materia.numero_ordem
        dic_expediente_materia["id_materia"] = (materia.tipo.sigla + ' ' +
                                                materia.tipo.descricao + ' ' +
                                                str(materia.numero) + '/' +
                                                str(materia.ano))
        dic_expediente_materia["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(
            materia=expediente_materia.materia).first()
        if numeracao is not None:
            dic_expediente_materia["des_numeracao"] = (
                str(numeracao.numero) + '/' + str(numeracao.ano))

        dic_expediente_materia["des_turno"] = ' '
        tram = Tramitacao.objects.filter(
            materia=materia).first()
        if tram is not None:
            if tram.turno != '':
                for turno in [("P", _("Primeiro")),
                              ("S", _("Segundo")),
                              ("U", _("Único")),
                              ("L", _("Suplementar")),
                              ("A", _("Votação Única em Regime de Urgência")),
                              ("B", _("1ª Votação")),
                              ("C", _("2ª e 3ª Votações")),
                              ("F", "Final")]:
                    if tram.turno == turno[0]:
                        dic_expediente_materia["des_turno"] = turno[1]

        dic_expediente_materia["txt_ementa"] = str(materia.ementa)
        dic_expediente_materia["ordem_observacao"] = ' '  # TODO
        dic_expediente_materia["nom_autor"] = ' '

        autoria = Autoria.objects.filter(
            materia=materia, primeiro_autor=True).first()

        if autoria is not None:
            autor = Autor.objects.filter(id=autoria.autor.id)

            if autor is not None:
                autor = autor.first()

            if autor.tipo == 'Parlamentar':
                parlamentar = Parlamentar.objects.filter(
                    id=autor.parlamentar.id)
                dic_expediente_materia["nom_autor"] = str(
                    parlamentar.nome_completo)
            elif autor.tipo == 'Comissao':
                comissao = Comissao.objects.filter(id=autor.comissao.id)
                dic_expediente_materia["nom_autor"] = str(comissao)
            else:
                dic_expediente_materia["nom_autor"] = str(autor.nome)
        elif autoria is None:
            dic_expediente_materia["nom_autor"] = 'Desconhecido'

        dic_expediente_materia["votacao_observacao"] = ' '
        if not expediente_materia.resultado:
            resultado = RegistroVotacao.objects.filter(
                tipo_resultado_votacao=expediente_materia.tipo_votacao)

            for i in resultado:
                dic_expediente_materia["nom_resultado"] = (
                    i.tipo_resultado_votacao.nome)
                dic_expediente_materia["votacao_observacao"] = (
                    expediente_materia.observacao)
        else:
            dic_expediente_materia["nom_resultado"] = _("Matéria não votada")
            dic_expediente_materia["votacao_observacao"] = _("Vazio")
        lst_expediente_materia.append(dic_expediente_materia)

    # Lista dos oradores do Expediente
    lst_oradores_expediente = []
    for orador_expediente in OradorExpediente.objects.filter(
            sessao_plenaria=sessao):
        parlamentar = Parlamentar.objects.get(
            id=orador_expediente.parlamentar.id)
        dic_oradores_expediente = {}
        dic_oradores_expediente["num_ordem"] = (
            orador_expediente.numero_ordem)
        dic_oradores_expediente["nom_parlamentar"] = (
            parlamentar.nome_parlamentar)
        dic_oradores_expediente['sgl_partido'] = (
            Filiacao.objects.filter(
                parlamentar=parlamentar).first().partido.sigla)
        lst_oradores_expediente.append(dic_oradores_expediente)

    # Lista presença na ordem do dia
    lst_presenca_ordem_dia = []
    for presenca_ordem_dia in PresencaOrdemDia.objects.filter(
            sessao_plenaria=sessao):
        for parlamentar in Parlamentar.objects.filter(
                id=presenca_ordem_dia.parlamentar.id):
            dic_presenca_ordem_dia = {}
            dic_presenca_ordem_dia['nom_parlamentar'] = (
                parlamentar.nome_parlamentar)
            dic_presenca_ordem_dia['sgl_partido'] = (
                Filiacao.objects.filter(
                    parlamentar=parlamentar).first().partido.sigla)
            lst_presenca_ordem_dia.append(dic_presenca_ordem_dia)

    # Lista das matérias da Ordem do Dia, incluindo o resultado das votacoes
    lst_votacao = []
    for votacao in OrdemDia.objects.filter(
            sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = MateriaLegislativa.objects.filter(
            id=votacao.materia.id).first()

        dic_votacao = {}
        dic_votacao["num_ordem"] = votacao.numero_ordem
        dic_votacao["id_materia"] = (
            materia.tipo.sigla + ' ' +
            materia.tipo.descricao + ' ' +
            str(materia.numero) + '/' +
            str(materia.ano))
        dic_votacao["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(
            materia=votacao.materia).first()
        if numeracao is not None:
            dic_votacao["des_numeracao"] = (
                str(numeracao.numero) +
                '/' +
                str(numeracao.ano))
        dic_votacao["des_turno"] = ' '

        tramitacao = Tramitacao.objects.filter(
            materia=materia).first()
        if tramitacao is not None:
            if not tramitacao.turno:
                for turno in [("P", _("Primeiro")),
                              ("S", _("Segundo")),
                              ("U", _("Único")),
                              ("L", _("Suplementar")),
                              ("F", _("Final")),
                              ("A", _("Votação Única em Regime de Urgência")),
                              ("B", _("1ª Votação")),
                              ("C", _("2ª e 3ª Votações"))]:
                    if tramitacao.turno == turno[0]:
                        dic_votacao["des_turno"] = turno[1]

        dic_votacao["txt_ementa"] = materia.ementa
        dic_votacao["ordem_observacao"] = votacao.observacao

        dic_votacao["nom_autor"] = ' '
        autoria = Autoria.objects.filter(
            materia=materia, primeiro_autor=True).first()

        if autoria is not None:
            autor = Autor.objects.filter(id=autoria.autor.id)
            if autor is not None:
                autor = autor.first()

            if autor.tipo == 'Parlamentar':
                parlamentar = Parlamentar.objects.filter(
                    id=autor.parlamentar.id)
                dic_votacao["nom_autor"] = str(parlamentar.nome_completo)
            elif autor.tipo == 'Comissao':
                comissao = Comissao.objects.filter(
                    id=autor.comissao.id)
                dic_votacao["nom_autor"] = str(comissao)
            else:
                dic_votacao["nom_autor"] = str(autor.nome)
        elif autoria is None:
            dic_votacao["nom_autor"] = 'Desconhecido'

        dic_votacao["votacao_observacao"] = ' '
        if not votacao.resultado:
            resultado = RegistroVotacao.objects.filter(
                tipo_resultado_votacao=votacao.tipo_votacao)
            for i in resultado:
                dic_votacao["nom_resultado"] = i.tipo_resultado_votacao.nome
                if votacao.observacao:
                    dic_votacao["votacao_observacao"] = votacao.observacao
        else:
            dic_votacao["nom_resultado"] = _("Matéria não votada")
            dic_votacao["votacao_observacao"] = _("Vazio")
        lst_votacao.append(dic_votacao)

    # Lista dos oradores nas Explicações Pessoais
    lst_oradores = []
    for orador in Orador.objects.filter(
            sessao_plenaria=sessao):
        for parlamentar in Parlamentar.objects.filter(
                id=orador.parlamentar.id):
            dic_oradores = {}
            dic_oradores["num_ordem"] = orador.numero_ordem
            dic_oradores["nom_parlamentar"] = parlamentar.nome_parlamentar
            dic_oradores['sgl_partido'] = (
                Filiacao.objects.filter(
                    parlamentar=parlamentar).first().partido.sigla)
            lst_oradores.append(dic_oradores)

    return (inf_basicas_dic,
            lst_mesa,
            lst_presenca_sessao,
            lst_expedientes,
            lst_expediente_materia,
            lst_oradores_expediente,
            lst_presenca_ordem_dia,
            lst_votacao,
            lst_oradores)


def relatorio_sessao_plenaria(request, pk):
    '''
        pdf_sessao_plenaria_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        'attachment; filename="relatorio_protocolo.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    sessao = SessaoPlenaria.objects.get(id=pk)

    (inf_basicas_dic,
     lst_mesa,
     lst_presenca_sessao,
     lst_expedientes,
     lst_expediente_materia,
     lst_oradores_expediente,
     lst_presenca_ordem_dia,
     lst_votacao,
     lst_oradores) = get_sessao_plenaria(sessao, casa)

    pdf = pdf_sessao_plenaria_gerar.principal(
        cabecalho,
        rodape,
        imagem,
        None,
        inf_basicas_dic,
        lst_mesa,
        lst_presenca_sessao,
        lst_expedientes,
        lst_expediente_materia,
        lst_oradores_expediente,
        lst_presenca_ordem_dia,
        lst_votacao,
        lst_oradores)

    response.write(pdf)
    return response


def get_protocolos(prots):

    protocolos = []
    for protocolo in prots:
        dic = {}

        dic['titulo'] = str(protocolo.numero) + '/' + str(protocolo.ano)

        dic['data'] = protocolo.data.strftime(
            "%d/%m/%Y") + ' - <b>Horário:</b>' + protocolo.hora.strftime(
            "%H:%m")

        dic['txt_assunto'] = protocolo.assunto_ementa

        dic['txt_interessado'] = protocolo.interessado

        dic['nom_autor'] = " "

        if protocolo.autor:
            if protocolo.autor.parlamentar:
                dic['nom_autor'] = protocolo.autor.parlamentar.nome_completo
            elif protocolo.autor.comissao:
                dic['nom_autor'] = protocolo.autor.comissao.nome

        dic['natureza'] = ''

        if protocolo.tipo_documento:
            dic['natureza'] = 'Administrativo'
            dic['processo'] = protocolo.tipo_documento.descricao
        elif protocolo.tipo_materia:
            dic['natureza'] = 'Legislativo'
            dic['processo'] = protocolo.tipo_materia.descricao
        else:
            dic['natureza'] = 'Indefinida'
            dic['processo'] = ''

        dic['anulado'] = ''
        if protocolo.anulado:
            dic['anulado'] = 'Nulo'

        protocolos.append(dic)

    return protocolos


def relatorio_protocolo(request):
    '''
        pdf_protocolo_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_protocolo.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    kwargs = get_kwargs_params(request, ['numero',
                                         'ano',
                                         'tipo_protocolo',
                                         'tipo_processo',
                                         'autor',
                                         'assunto__icontains',
                                         'interessado__icontains'])

    protocolos = Protocolo.objects.filter(**kwargs)

    protocolo_data = get_protocolos(protocolos)

    pdf = pdf_protocolo_gerar.principal(imagem,
                                        protocolo_data,
                                        cabecalho,
                                        rodape)

    response.write(pdf)

    return response


def relatorio_etiqueta_protocolo(request, nro, ano):
    '''
        pdf_etiqueta_protocolo_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_etiqueta_protocolo.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    protocolo = Protocolo.objects.filter(numero=nro, ano=ano)

    protocolo_data = get_etiqueta_protocolos(protocolo)

    pdf = pdf_etiqueta_protocolo_gerar.principal(imagem,
                                                 protocolo_data,
                                                 cabecalho,
                                                 rodape)

    response.write(pdf)

    return response


def get_etiqueta_protocolos(prots):

    protocolos = []
    for p in prots:
        dic = {}

        dic['titulo'] = str(p.numero) + '/' + str(p.ano)
        dic['data'] = '<b>Data: </b>' + p.data.strftime(
            "%d/%m/%Y") + ' - <b>Horário: </b>' + p.hora.strftime("%H:%m")
        dic['txt_assunto'] = p.assunto_ementa
        dic['txt_interessado'] = p.interessado

        dic['nom_autor'] = ' '

        if p.autor:
            if p.autor.parlamentar:
                dic['nom_autor'] = p.autor.parlamentar.nome_completo
            elif p.autor.comissao:
                dic['nom_autor'] = p.autor.comissao.nome

        dic['natureza'] = ''
        if p.tipo_processo == 0:
            dic['natureza'] = 'Administrativo'
        if p.tipo_processo == 1:
            dic['natureza'] = 'Legislativo'

        dic['num_materia'] = ''
        for materia in MateriaLegislativa.objects.filter(
                numero_protocolo=p.numero, ano=p.ano):
            dic['num_materia'] = str(materia)

        dic['num_documento'] = ''
        for documento in DocumentoAdministrativo.objects.filter(
                numero_protocolo=p.numero):
            dic['num_documento'] = str(documento)

        dic['ident_processo'] = dic['num_materia'] or dic['num_documento']

        dic['processo'] = (str(p.tipo_materia) or
                           str(p.tipo_documento))

        dic['anulado'] = ''
        if p.anulado:
            dic['anulado'] = 'Nulo'

        protocolos.append(dic)
    return protocolos


def relatorio_pauta_sessao(request):
    '''
        pdf__pauta_sessao_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'attachment; filename="relatorio_pauta_sessao.pdf"')

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    sessao = SessaoPlenaria.objects.first()

    lst_expediente_materia, lst_votacao, inf_basicas_dic = get_pauta_sessao(
        sessao, casa)
    pdf = pdf_pauta_sessao_gerar.principal(cabecalho,
                                           rodape,
                                           sessao,
                                           imagem,
                                           inf_basicas_dic,
                                           lst_expediente_materia,
                                           lst_votacao)

    response.write(pdf)

    return response


def get_pauta_sessao(sessao, casa):

    inf_basicas_dic = {}
    inf_basicas_dic["nom_sessao"] = sessao.tipo.nome
    inf_basicas_dic["num_sessao_plen"] = sessao.numero
    inf_basicas_dic["num_legislatura"] = sessao.legislatura
    inf_basicas_dic["num_sessao_leg"] = sessao.legislatura
    inf_basicas_dic["dat_inicio_sessao"] = sessao.data_inicio
    inf_basicas_dic["hr_inicio_sessao"] = sessao.hora_inicio
    inf_basicas_dic["dat_fim_sessao"] = sessao.data_fim
    inf_basicas_dic["hr_fim_sessao"] = sessao.hora_fim
    inf_basicas_dic["nom_camara"] = casa.nome

    lst_expediente_materia = []
    for expediente_materia in ExpedienteMateria.objects.filter(
            data_ordem=sessao.data_inicio, sessao_plenaria=sessao):

        materia = MateriaLegislativa.objects.filter(
            id=expediente_materia.materia.id).first()

        dic_expediente_materia = {}
        dic_expediente_materia["num_ordem"] = str(
            expediente_materia.numero_ordem)
        dic_expediente_materia["id_materia"] = str(
            materia.numero) + "/" + str(materia.ano)
        dic_expediente_materia["txt_ementa"] = materia.ementa
        dic_expediente_materia["ordem_observacao"] = str(
            expediente_materia.observacao)

        dic_expediente_materia["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(materia=materia)
        if numeracao is not None:
            numeracao = numeracao.first()
            dic_expediente_materia["des_numeracao"] = str(numeracao)

        dic_expediente_materia["nom_autor"] = ' '
        autoria = Autoria.objects.filter(
            materia=materia, primeiro_autor=True).first()

        if autoria is not None:
            autor = Autor.objects.filter(id=autoria.autor.id)

            if autor is not None:
                autor = autor.first()

            if autor.tipo == 'Parlamentar':
                parlamentar = Parlamentar.objects.filter(
                    id=autor.parlamentar.id)
                dic_expediente_materia["nom_autor"] = str(
                    parlamentar.nome_completo)
            elif autor.tipo == 'Comissao':
                comissao = Comissao.objects.filter(id=autor.comissao.id)
                dic_expediente_materia["nom_autor"] = str(comissao)
            else:
                dic_expediente_materia["nom_autor"] = str(autor.nome)
        elif autoria is None:
            dic_expediente_materia["nom_autor"] = 'Desconhecido'

        dic_expediente_materia["des_turno"] = ' '
        dic_expediente_materia["des_situacao"] = ' '

        tramitacao = Tramitacao.objects.filter(materia=materia)
        if tramitacao is not None:
            tramitacao = tramitacao.first()

            if tramitacao.turno != '':
                for turno in [("P", _("Primeiro")),
                              ("S", _("Segundo")),
                              ("U", _("Único")),
                              ("F", _("Final")),
                              ("L", _("Suplementar")),
                              ("A", _("Votação Única em Regime de Urgência")),
                              ("B", _("1ª Votação")),
                              ("C", _("2ª e 3ª Votações"))]:
                    if tramitacao.turno == turno.first():
                        dic_expediente_materia["des_turno"] = turno.first()

            dic_expediente_materia["des_situacao"] = tramitacao.status
            if dic_expediente_materia["des_situacao"] is None:
                dic_expediente_materia["des_situacao"] = ' '
        lst_expediente_materia.append(dic_expediente_materia)

    lst_votacao = []
    for votacao in OrdemDia.objects.filter(
            data_ordem=sessao.data_inicio, sessao_plenaria=sessao):
        materia = MateriaLegislativa.objects.filter(
            id=votacao.materia.id).first()
        dic_votacao = {}
        dic_votacao["num_ordem"] = votacao.numero_ordem
        dic_votacao["id_materia"] = str(
            materia.numero) + "/" + str(materia.ano)
        dic_votacao["txt_ementa"] = materia.ementa
        dic_votacao["ordem_observacao"] = votacao.observacao

        dic_votacao["des_numeracao"] = ' '
        numeracao = Numeracao.objects.filter(materia=materia)
        # if numeracao is not None:
        #     numeracao = numeracao.first()
        #     dic_votacao["des_numeracao"] = str(
        #         numeracao.numero) + '/' + str(numeracao.ano)

        dic_votacao["nom_autor"] = ' '
        autoria = Autoria.objects.filter(
            materia=materia, primeiro_autor=True).first()

        if autoria is not None:
            autor = Autor.objects.filter(id=autoria.autor.id)
            if autor is not None:
                autor = autor.first()

            if autor.tipo == 'Parlamentar':
                parlamentar = Parlamentar.objects.filter(
                    id=autor.parlamentar.id)
                dic_votacao["nom_autor"] = str(parlamentar.nome_completo)
            elif autor.tipo == 'Comissao':
                comissao = Comissao.objects.filter(
                    id=autor.comissao.id)
                dic_votacao["nom_autor"] = str(comissao)
            else:
                dic_votacao["nom_autor"] = str(autor.nome)
        elif autoria is None:
            dic_votacao["nom_autor"] = 'Desconhecido'

        dic_votacao["des_turno"] = ' '
        dic_votacao["des_situacao"] = ' '
        tramitacao = Tramitacao.objects.filter(materia=materia)
        if tramitacao is not None:
            tramitacao = tramitacao.first()
            if tramitacao.turno != '':
                for turno in [("P", _("Primeiro")),
                              ("S", _("Segundo")),
                              ("U", _("Único")),
                              ("L", _("Suplementar")),
                              ("A", _("Votação Única em Regime de Urgência")),
                              ("B", _("1ª Votação")),
                              ("C", _("2ª e 3ª Votações"))]:
                    if tramitacao.turno == turno.first():
                        dic_votacao["des_turno"] = turno.first()

            dic_votacao["des_situacao"] = tramitacao.status
            if dic_votacao["des_situacao"] is None:
                dic_votacao["des_situacao"] = ' '
        lst_votacao.append(dic_votacao)

    return (lst_expediente_materia,
            lst_votacao,
            inf_basicas_dic)
