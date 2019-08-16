from datetime import datetime as dt
import html
import logging
import re
import tempfile


from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from sapl.settings import MEDIA_URL
from sapl.base.models import Autor, CasaLegislativa
from sapl.comissoes.models import Comissao
from sapl.materia.models import (Autoria, MateriaLegislativa, Numeracao,
                                 Tramitacao, UnidadeTramitacao)
from sapl.parlamentares.models import CargoMesa, Filiacao, Parlamentar
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      TramitacaoAdministrativo)
from sapl.sessao.models import (ExpedienteMateria, ExpedienteSessao,
                                IntegranteMesa, JustificativaAusencia,
                                Orador, OradorExpediente,
                                OrdemDia, PresencaOrdemDia, SessaoPlenaria,
                                SessaoPlenariaPresenca, OcorrenciaSessao,
                                RegistroVotacao, VotoParlamentar, OradorOrdemDia, TipoExpediente)
from sapl.settings import STATIC_ROOT
from sapl.utils import LISTA_DE_UFS, TrocaTag, filiacao_data

from sapl.sessao.views import (get_identificacao_basica, get_mesa_diretora,
                               get_presenca_sessao, get_expedientes,
                               get_materias_expediente, get_oradores_expediente,
                               get_presenca_ordem_do_dia, get_materias_ordem_do_dia,
                               get_oradores_ordemdia,
                               get_oradores_explicacoes_pessoais, get_ocorrencias_da_sessao, get_assinaturas)

from .templates import (pdf_capa_processo_gerar,
                        pdf_documento_administrativo_gerar, pdf_espelho_gerar,
                        pdf_etiqueta_protocolo_gerar, pdf_materia_gerar,
                        pdf_ordem_dia_gerar, pdf_pauta_sessao_gerar,
                        pdf_protocolo_gerar, pdf_sessao_plenaria_gerar)

from weasyprint import HTML, CSS


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
    uf_dict = dict(LISTA_DE_UFS)
    # FIXME i18n
    cabecalho["nom_estado"] = "Estado de " + uf_dict[casa.uf.upper()]
    return cabecalho


def get_imagem(casa):
    if casa.logotipo:
        return casa.logotipo.path
    return STATIC_ROOT + '/img/brasao_transp.gif'


def get_rodape(casa):

    if len(casa.cep) == 8:
        cep = casa.cep[:4] + "-" + casa.cep[5:]
    else:
        cep = ""

    linha1 = casa.endereco

    if cep:
        if casa.endereco:
            linha1 = linha1 + " - "
        linha1 = linha1 + str(_("CEP ")) + cep

    # substituindo nom_localidade por municipio e sgl_uf por uf
    if casa.municipio:
        linha1 = linha1 + " - " + casa.municipio + " " + casa.uf

    if casa.telefone:
        linha1 = linha1 + str(_(" Tel.: ")) + casa.telefone

    if casa.endereco_web:
        linha2 = casa.endereco_web
    else:
        linha2 = ""

    if casa.email:
        if casa.endereco_web:
            linha2 = linha2 + " - "
        linha2 = linha2 + str(_("E-mail: ")) + casa.email

    data_emissao = dt.strftime(timezone.now(), "%d/%m/%Y")

    return [linha1, linha2, data_emissao]


def get_materias(mats):

    materias = []
    for materia in mats:
        dic = {}
        dic['titulo'] = materia.tipo.sigla + " " + materia.tipo.descricao \
            + " " + str(materia.numero) + "/" + str(materia.ano)
        dic['txt_ementa'] = materia.ementa

        dic['nom_autor'] = ', '.join(
            [str(autor) for autor in materia.autores.all()])

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
    response['Content-Disposition'] = (
        'inline; filename="relatorio_materia.pdf"')

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

        if p.autor:
            dic['nom_autor'] = str(p.autor or ' ')
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
        'Content-Disposition'] = ('inline; filename="relatorio_processo.pdf"')

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

    response['Content-Disposition'] = (
        'inline; filename="relatorio_ordem_dia.pdf"')

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
    response['Content-Disposition'] = (
        'inline; filename="relatorio_documento_administrativo.pdf"')

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
    response['Content-Disposition'] = (
        'inline; filename="relatorio_espelho.pdf"')

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

        dic['nom_autor'] = []
        for autoria in Autoria.objects.filter(materia=m, primeiro_autor=True):
            dic['nom_autor'].append(str(autoria.autor))

        dic['nom_autor'] = ', '.join(dic['nom_autor'])

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

        dic['norma_juridica_vinculada'] = str(_('Não há nenhuma \
                                           norma jurídica vinculada'))
        # TODO
        # for norma in context.zsql.materia_buscar_norma_juridica_zsql(
        #       cod_materia=materia.cod_materia):
        #     dic['norma_juridica_vinculada'] = norma.des_norma + " " + \
        #         str(norma.num_norma) + "/" + str(norma.ano_norma)

        materias.append(dic)
    return materias


def remove_html_comments(text):
    """
        Assume comentários bem formados <!-- texto --> e
        não aninhados como <!-- <!-- texto --> -->
    :param text:
    :return:
    """
    clean_text = text
    start = clean_text.find('<!--')
    while start > -1:
        end = clean_text.find('-->') + 2
        output_text = []
        for idx, i in enumerate(clean_text):
            if not start <= idx <= end:
                output_text.append(i)
        clean_text = ''.join(output_text)
        start = clean_text.find('<!--')

    # por algum motivo usar clean_text ao invés de len(clean_text)
    #  não tava funcionando
    return clean_text if len(clean_text) > 0 else text


def get_sessao_plenaria(sessao, casa):

    inf_basicas_dic = {}
    inf_basicas_dic["num_sessao_plen"] = str(sessao.numero)
    inf_basicas_dic["nom_sessao"] = sessao.tipo.nome
    inf_basicas_dic["num_legislatura"] = str(sessao.legislatura)
    inf_basicas_dic["num_sessao_leg"] = sessao.sessao_legislativa.numero
    inf_basicas_dic["dat_inicio_sessao"] = sessao.data_inicio.strftime(
        "%d/%m/%Y")
    inf_basicas_dic["hr_inicio_sessao"] = sessao.hora_inicio
    if sessao.data_fim:
        inf_basicas_dic["dat_fim_sessao"] = \
            sessao.data_fim.strftime("%d/%m/%Y")
    else:
        inf_basicas_dic["dat_fim_sessao"] = ''
    inf_basicas_dic["hr_fim_sessao"] = sessao.hora_fim
    inf_basicas_dic["nom_camara"] = casa.nome

    if sessao.tipo.nome == 'Solene':
        inf_basicas_dic["tema_solene"] = sessao.tema_solene
    
    # Conteudo multimidia
    cont_mult_dic = {}
    if sessao.url_audio:
        cont_mult_dic['multimidia_audio'] = str(sessao.url_audio)
    else:
        cont_mult_dic['multimidia_audio'] = 'Indisponível'
    
    if sessao.url_video:
        cont_mult_dic['multimidia_video'] = str(sessao.url_video)
    else:
        cont_mult_dic['multimidia_video'] = 'Indisponível'

    # Lista da composicao da mesa diretora
    lst_mesa = []
    for composicao in IntegranteMesa.objects.filter(sessao_plenaria=sessao):
        for parlamentar in Parlamentar.objects.filter(
                id=composicao.parlamentar.id):
            for cargo in CargoMesa.objects.filter(id=composicao.cargo.id):
                dic_mesa = {}
                dic_mesa['nom_parlamentar'] = parlamentar.nome_parlamentar
                partido_sigla = Filiacao.objects.filter(
                    parlamentar=parlamentar).first()
                if not partido_sigla:
                    sigla = ''
                else:
                    sigla = partido_sigla.partido.sigla
                dic_mesa['sgl_partido'] = sigla
                dic_mesa['des_cargo'] = cargo.descricao
                lst_mesa.append(dic_mesa)

    # Lista de presença na sessão
    lst_presenca_sessao = []
    presenca = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).order_by('parlamentar__nome_parlamentar')

    for parlamentar in [p.parlamentar for p in presenca]:
        dic_presenca = {}
        dic_presenca["nom_parlamentar"] = parlamentar.nome_parlamentar
        partido_sigla = filiacao_data(parlamentar, sessao.data_inicio)

        dic_presenca['sgl_partido'] = partido_sigla
        lst_presenca_sessao.append(dic_presenca)

    # Lista de ausencias na sessão
    lst_ausencia_sessao = []
    ausencia = JustificativaAusencia.objects.filter(
        sessao_plenaria=sessao).order_by('parlamentar__nome_parlamentar')
    for ausente in ausencia:
        dic_ausencia = {}
        dic_ausencia['parlamentar'] = ausente.parlamentar
        dic_ausencia['justificativa'] = ausente.tipo_ausencia
        if ausente.ausencia == 1:
            dic_ausencia['tipo'] = 'Matéria'
        else:
            dic_ausencia['tipo'] = 'Sessão'

        lst_ausencia_sessao.append(dic_ausencia)

    # Exibe os Expedientes
    lst_expedientes = []
    expedientes = ExpedienteSessao.objects.filter(
        sessao_plenaria=sessao).order_by('tipo__nome')

    for e in expedientes:
        dic_expedientes = {}
        dic_expedientes["nom_expediente"] = e.tipo.nome
        conteudo = e.conteudo

        # unescape HTML codes
        # https://github.com/interlegis/sapl/issues/1046
        conteudo = re.sub('style=".*?"', '', conteudo)
        conteudo = re.sub('class=".*?"', '', conteudo)
        conteudo = re.sub('align=".*?"', '', conteudo)    # OSTicket Ticket #796450
        conteudo = re.sub('<p\s+>', '<p>', conteudo)
        conteudo = re.sub('<br\s+/>', '<br/>', conteudo)  # OSTicket Ticket #796450
        conteudo = html.unescape(conteudo)

        # escape special character '&'
        #   https://github.com/interlegis/sapl/issues/1009
        conteudo = conteudo.replace('&', '&amp;')

        # https://github.com/interlegis/sapl/issues/2386
        conteudo = remove_html_comments(conteudo)

        dic_expedientes["txt_expediente"] = conteudo

        if dic_expedientes:
            lst_expedientes.append(dic_expedientes)

    # Lista das matérias do Expediente, incluindo o resultado das votacoes
    lst_expediente_materia = []
    for expediente_materia in ExpedienteMateria.objects.filter(
            sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = expediente_materia.materia
        dic_expediente_materia = {}
        dic_expediente_materia["num_ordem"] = expediente_materia.numero_ordem
        dic_expediente_materia["id_materia"] = (materia.tipo.sigla + ' ' +
                                                materia.tipo.descricao + ' ' +
                                                str(materia.numero) + '/' +
                                                str(materia.ano))
        dic_expediente_materia["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(
            materia=expediente_materia.materia).first()
        if numeracao:
            dic_expediente_materia["des_numeracao"] = (
                str(numeracao.numero_materia) + '/' + str(
                    numeracao.ano_materia))

        turno, _ = get_turno(materia)

        dic_expediente_materia["des_turno"] = turno
        dic_expediente_materia["txt_ementa"] = str(materia.ementa)
        dic_expediente_materia["ordem_observacao"] = expediente_materia.observacao
        dic_expediente_materia["nom_resultado"] = ''

        dic_expediente_materia["nom_autor"] = ''
        autoria = materia.autoria_set.all()
        dic_expediente_materia['num_autores'] = 'Autores' if len(
            autoria) > 1 else 'Autor'
        if autoria:
            for a in autoria:
                if a.autor.nome:
                    dic_expediente_materia['nom_autor'] += a.autor.nome + ', '
            dic_expediente_materia['nom_autor'] = dic_expediente_materia['nom_autor'][:-2]
        else:
            dic_expediente_materia["nom_autor"] = 'Desconhecido'

        dic_expediente_materia["votacao_observacao"] = ' '
        resultados = expediente_materia.registrovotacao_set.all()
        if resultados:
            for i in resultados:
                dic_expediente_materia["nom_resultado"] = (
                    i.tipo_resultado_votacao.nome)
                dic_expediente_materia["votacao_observacao"] = (
                    i.observacao)
        else:
            dic_expediente_materia["nom_resultado"] = 'Matéria não votada'
            dic_expediente_materia["votacao_observacao"] = ' '
        lst_expediente_materia.append(dic_expediente_materia)

    # Lista dos votos nominais das matérias do Expediente
    lst_expediente_materia_vot_nom = []

    materias_expediente_votacao_nominal = ExpedienteMateria.objects.filter(
        sessao_plenaria=sessao,
        tipo_votacao=2).order_by('-materia')
    
    for mevn in materias_expediente_votacao_nominal:
        votos_materia = []
        titulo_materia = mevn.materia
        registro = RegistroVotacao.objects.filter(expediente=mevn)
        
        if registro:
            for vp in VotoParlamentar.objects.filter(votacao=registro).order_by('parlamentar'):
                votos_materia.append(vp)
        
        dic_expediente_materia_vot_nom = {
            'titulo': titulo_materia,
            'votos': votos_materia
        } 
        lst_expediente_materia_vot_nom.append(dic_expediente_materia_vot_nom)

    # Lista dos oradores do Expediente
    lst_oradores_expediente = []
    for orador_expediente in OradorExpediente.objects.filter(
            sessao_plenaria=sessao).order_by('numero_ordem'):
        parlamentar = Parlamentar.objects.get(
            id=orador_expediente.parlamentar.id)
        dic_oradores_expediente = {}
        dic_oradores_expediente["num_ordem"] = (
            orador_expediente.numero_ordem)
        dic_oradores_expediente["nom_parlamentar"] = (
            parlamentar.nome_parlamentar)
        dic_oradores_expediente["observacao"] = (
            orador_expediente.observacao)
        partido_sigla = Filiacao.objects.filter(
            parlamentar=parlamentar).first()
        if not partido_sigla:
            sigla = ''
        else:
            sigla = partido_sigla.partido.sigla
        dic_oradores_expediente['sgl_partido'] = sigla
        lst_oradores_expediente.append(dic_oradores_expediente)

    # Lista presença na ordem do dia
    lst_presenca_ordem_dia = []
    presenca_ordem_dia = PresencaOrdemDia.objects.filter(
        sessao_plenaria=sessao).order_by('parlamentar__nome_parlamentar')
    for parlamentar in [p.parlamentar for p in presenca_ordem_dia]:
        dic_presenca_ordem_dia = {}
        dic_presenca_ordem_dia['nom_parlamentar'] = (
            parlamentar.nome_parlamentar)
        sigla = filiacao_data(parlamentar, sessao.data_inicio)

        dic_presenca_ordem_dia['sgl_partido'] = sigla
        lst_presenca_ordem_dia.append(dic_presenca_ordem_dia)

    # Lista das matérias da Ordem do Dia, incluindo o resultado das votacoes
    lst_votacao = []
    for votacao in OrdemDia.objects.filter(
            sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = votacao.materia
        dic_votacao = {}
        dic_votacao["nom_resultado"] = ''
        dic_votacao["num_ordem"] = votacao.numero_ordem
        dic_votacao["id_materia"] = (
            materia.tipo.sigla + ' ' +
            materia.tipo.descricao + ' ' +
            str(materia.numero) + '/' +
            str(materia.ano))
        dic_votacao["des_numeracao"] = ' '

        numeracao = materia.numeracao_set.first()
        if numeracao:

            dic_votacao["des_numeracao"] = (
                str(numeracao.numero_materia) +
                '/' +
                str(numeracao.ano_materia))

        turno, _ = get_turno(materia)

        dic_votacao["des_turno"] = turno

        # https://github.com/interlegis/sapl/issues/1009
        dic_votacao["txt_ementa"] = html.unescape(materia.ementa)
        dic_votacao["ordem_observacao"] = html.unescape(votacao.observacao)

        dic_votacao["nom_autor"] = ''
        autoria = materia.autoria_set.all()
        dic_votacao['num_autores'] = 'Autores' if len(autoria) > 1 else 'Autor'
        if autoria:
            for a in autoria:
                if a.autor.nome:
                    dic_votacao['nom_autor'] += a.autor.nome + ', '
            dic_votacao['nom_autor'] = dic_votacao['nom_autor'][:-2]
        else:
            dic_votacao["nom_autor"] = 'Desconhecido'

        dic_votacao["votacao_observacao"] = ' '
        resultados = votacao.registrovotacao_set.all()
        if resultados:
            for i in resultados:
                dic_votacao["nom_resultado"] = i.tipo_resultado_votacao.nome
                if i.observacao:
                    dic_votacao["votacao_observacao"] = i.observacao
        else:
            dic_votacao["nom_resultado"] = "Matéria não votada"
        lst_votacao.append(dic_votacao)

    # Lista dos votos nominais das matérias da Ordem do Dia
    lst_votacao_vot_nom = []

    materias_ordem_dia_votacao_nominal = OrdemDia.objects.filter(
        sessao_plenaria=sessao,
        tipo_votacao=2).order_by('-materia')
    
    for modvn in materias_ordem_dia_votacao_nominal:
        votos_materia_od = []
        t_materia = modvn.materia
        registro_od = RegistroVotacao.objects.filter(ordem=modvn)
        
        if registro_od:
            for vp_od in VotoParlamentar.objects.filter(votacao=registro_od).order_by('parlamentar'):
                votos_materia_od.append(vp_od)
        
        dic_votacao_vot_nom = {
            'titulo': t_materia,
            'votos': votos_materia_od
        } 
        lst_votacao_vot_nom.append(dic_votacao_vot_nom)

    # Lista dos oradores da Ordem do Dia
    lst_oradores_ordemdia = []

    oradores_ordem_dia = OradorOrdemDia.objects.filter(
        sessao_plenaria=sessao
    ).order_by('numero_ordem')

    for orador_ordemdia in oradores_ordem_dia:
        parlamentar_orador = Parlamentar.objects.get(
            id=orador_ordemdia.parlamentar.id
        )
        
        sigla_partido = Filiacao.objects.filter(
            parlamentar=parlamentar_orador
        ).first()

        if not sigla_partido:
            sigla_p = ""
        else:
            sigla_p = sigla_partido.partido.sigla
        
        dic_oradores_ordemdia = {
            'num_ordem': orador_ordemdia.numero_ordem,
            'nome_parlamentar': parlamentar_orador.nome_parlamentar,
            'observacao': orador_ordemdia.observacao,
            'sigla': sigla_p
        }
        lst_oradores_ordemdia.append(dic_oradores_ordemdia)

    # Lista dos oradores nas Explicações Pessoais
    lst_oradores = []
    for orador in Orador.objects.filter(
            sessao_plenaria=sessao).order_by('numero_ordem'):
        for parlamentar in Parlamentar.objects.filter(
                id=orador.parlamentar.id):
            dic_oradores = {}
            dic_oradores["num_ordem"] = orador.numero_ordem
            dic_oradores["nom_parlamentar"] = parlamentar.nome_parlamentar
            partido_sigla = Filiacao.objects.filter(
                parlamentar=parlamentar).first()
            if not partido_sigla:
                sigla = ''
            else:
                sigla = partido_sigla.partido.sigla
            dic_oradores['sgl_partido'] = sigla
            lst_oradores.append(dic_oradores)

    # Ocorrências da Sessão
    lst_ocorrencias = []
    ocorrencias = OcorrenciaSessao.objects.filter(
        sessao_plenaria=sessao)

    for o in ocorrencias:
        conteudo = o.conteudo

        # unescape HTML codes
        # https://github.com/interlegis/sapl/issues/1046
        conteudo = re.sub('style=".*?"', '', conteudo)
        conteudo = html.unescape(conteudo)

        # escape special character '&'
        #   https://github.com/interlegis/sapl/issues/1009
        conteudo = conteudo.replace('&', '&amp;')

        o.conteudo = conteudo

        lst_ocorrencias.append(o)

    return (inf_basicas_dic,
            cont_mult_dic,
            lst_mesa,
            lst_presenca_sessao,
            lst_ausencia_sessao,
            lst_expedientes,
            lst_expediente_materia,
            lst_expediente_materia_vot_nom,
            lst_oradores_expediente,
            lst_presenca_ordem_dia,
            lst_votacao,
            lst_votacao_vot_nom,
            lst_oradores_ordemdia,
            lst_oradores,
            lst_ocorrencias)


def get_turno(materia):
    descricao_turno = ''
    descricao_tramitacao = ''
    tramitacao = materia.tramitacao_set.last()

    if tramitacao:
        if tramitacao.turno:
            for t in Tramitacao.TURNO_CHOICES:
                if t[0] == tramitacao.turno:
                    descricao_turno = str(t[1])
                    break
        descricao_tramitacao = tramitacao.status.descricao if tramitacao.status else 'Não informada'
    return descricao_turno, descricao_tramitacao


def relatorio_sessao_plenaria(request, pk):
    '''
        pdf_sessao_plenaria_gerar.py
    '''
    logger = logging.getLogger(__name__)
    username = request.user.username
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = (
        'inline; filename="relatorio_protocolo.pdf"')

    casa = CasaLegislativa.objects.first()

    if not casa:
        raise Http404

    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    try:
        logger.debug("user=" + username +
                     ". Tentando obter SessaoPlenaria com id={}.".format(pk))
        sessao = SessaoPlenaria.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        logger.error("user=" + username +
                     ". Essa SessaoPlenaria não existe (pk={}). ".format(pk) + str(e))
        raise Http404('Essa página não existe')

    (inf_basicas_dic,
     cont_mult_dic,
     lst_mesa,
     lst_presenca_sessao,
     lst_ausencia_sessao,
     lst_expedientes,
     lst_expediente_materia,
     lst_expediente_materia_vot_nom,
     lst_oradores_expediente,
     lst_presenca_ordem_dia,
     lst_votacao,
     lst_votacao_vot_nom,
     lst_oradores_ordemdia, 
     lst_oradores,
     lst_ocorrencias) = get_sessao_plenaria(sessao, casa)

    for idx in range(len(lst_expedientes)):
        txt_expedientes = lst_expedientes[idx]['txt_expediente']
        txt_expedientes = TrocaTag(txt_expedientes, '<table', 'table>', 6, 6,
                                   'expedientes', '</para><blockTable style = "', 'blockTable><para>')
        lst_expedientes[idx]['txt_expediente'] = txt_expedientes

    pdf = pdf_sessao_plenaria_gerar.principal(
        rodape,
        imagem,
        inf_basicas_dic,
        cont_mult_dic,
        lst_mesa,
        lst_presenca_sessao,
        lst_ausencia_sessao,
        lst_expedientes,
        lst_expediente_materia,
        lst_expediente_materia_vot_nom,
        lst_oradores_expediente,
        lst_presenca_ordem_dia,
        lst_votacao,
        lst_votacao_vot_nom,
        lst_oradores_ordemdia,
        lst_oradores,
        lst_ocorrencias)

    response.write(pdf)
    return response


def get_protocolos(prots):

    protocolos = []
    for protocolo in prots:
        dic = {}

        dic['titulo'] = str(protocolo.numero) + '/' + str(protocolo.ano)

        ts = timezone.localtime(protocolo.timestamp)
        if protocolo.timestamp:
            dic['data'] = ts.strftime("%d/%m/%Y") + ' - <b>Horário:</b>' + \
                ts.strftime("%H:%m")
        else:
            dic['data'] = protocolo.data.strftime("%d/%m/%Y") + ' - <b>Horário:</b>' \
                + protocolo.hora.strftime("%H:%m")

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
            'inline; filename="relatorio_protocolo.pdf"')

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
            'inline; filename="relatorio_etiqueta_protocolo.pdf"')

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

        if p.timestamp:
            tz_hora = timezone.localtime(p.timestamp)
            dic['data'] = '<b>Data: </b>' + tz_hora.strftime(
                "%d/%m/%Y") + ' - <b>Horário: </b>' + tz_hora.strftime("%H:%M")
        else:
            dic['data'] = '<b>Data: </b>' + p.data.strftime(
                "%d/%m/%Y") + ' - <b>Horário: </b>' + p.hora.strftime("%H:%M")
        dic['txt_assunto'] = p.assunto_ementa
        dic['txt_interessado'] = p.interessado

        dic['nom_autor'] = str(p.autor or ' ')

        dic['num_materia'] = ''
        for materia in MateriaLegislativa.objects.filter(
                numero_protocolo=p.numero, ano=p.ano):
            dic['num_materia'] = materia.tipo.sigla + ' ' + \
                str(materia.numero) + '/' + str(materia.ano)

        dic['natureza'] = ''
        if p.tipo_processo == 0:
            dic['natureza'] = 'Administrativo'
        if p.tipo_processo == 1:
            dic['natureza'] = 'Legislativo'

        dic['num_documento'] = ''
        for documento in DocumentoAdministrativo.objects.filter(
                protocolo=p):
            dic['num_documento'] = documento.tipo.sigla + ' ' + \
                str(documento.numero) + '/' + str(documento.ano)

        dic['ident_processo'] = dic['num_materia'] or dic['num_documento']

        dic['processo'] = (str(p.tipo_materia) or
                           str(p.tipo_documento))

        dic['anulado'] = ''
        if p.anulado:
            dic['anulado'] = 'Nulo'

        protocolos.append(dic)
    return protocolos


def relatorio_pauta_sessao(request, pk):
    '''
        pdf__pauta_sessao_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = (
            'inline; filename="relatorio_pauta_sessao.pdf"')

    casa = CasaLegislativa.objects.first()

    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    sessao = SessaoPlenaria.objects.get(id=pk)

    lst_expediente_materia, lst_votacao, inf_basicas_dic, expedientes = get_pauta_sessao(
        sessao, casa)
    pdf = pdf_pauta_sessao_gerar.principal(rodape,
                                           imagem,
                                           inf_basicas_dic,
                                           lst_expediente_materia,
                                           lst_votacao,
                                           expedientes)

    response.write(pdf)

    return response


def get_pauta_sessao(sessao, casa):

    inf_basicas_dic = {}
    inf_basicas_dic["nom_sessao"] = sessao.tipo.nome
    inf_basicas_dic["num_sessao_plen"] = sessao.numero
    inf_basicas_dic["num_legislatura"] = sessao.legislatura
    inf_basicas_dic["num_sessao_leg"] = sessao.sessao_legislativa.numero
    inf_basicas_dic["dat_inicio_sessao"] = sessao.data_inicio
    inf_basicas_dic["hr_inicio_sessao"] = sessao.hora_inicio
    inf_basicas_dic["dat_fim_sessao"] = sessao.data_fim
    inf_basicas_dic["hr_fim_sessao"] = sessao.hora_fim
    inf_basicas_dic["nom_camara"] = casa.nome

    lst_expediente_materia = []
    for expediente_materia in ExpedienteMateria.objects.filter(sessao_plenaria=sessao):

        materia = MateriaLegislativa.objects.filter(
            id=expediente_materia.materia.id).first()

        dic_expediente_materia = {}
        dic_expediente_materia["tipo_materia"] = materia.tipo.sigla + \
            ' - ' + materia.tipo.descricao
        dic_expediente_materia["num_ordem"] = str(
            expediente_materia.numero_ordem)
        dic_expediente_materia["id_materia"] = str(
            materia.numero) + "/" + str(materia.ano)
        dic_expediente_materia["txt_ementa"] = materia.ementa
        dic_expediente_materia["ordem_observacao"] = str(
            expediente_materia.observacao)

        dic_expediente_materia["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(materia=materia)
        if numeracao:
            numeracao = numeracao.first()
            dic_expediente_materia["des_numeracao"] = str(numeracao)

        dic_expediente_materia["nom_autor"] = ''
        autoria = materia.autoria_set.all()
        dic_expediente_materia['num_autores'] = 'Autores' if len(
            autoria) > 1 else 'Autor'
        if autoria:
            for a in autoria:
                if a.autor.nome:
                    dic_expediente_materia['nom_autor'] += a.autor.nome + ', '
            dic_expediente_materia['nom_autor'] = dic_expediente_materia['nom_autor'][:-2]
        else:
            dic_expediente_materia["nom_autor"] = 'Desconhecido'

        turno, tramitacao = get_turno(materia)

        dic_expediente_materia["des_turno"] = turno
        dic_expediente_materia["des_situacao"] = tramitacao

        lst_expediente_materia.append(dic_expediente_materia)

    lst_votacao = []
    for votacao in OrdemDia.objects.filter(
            sessao_plenaria=sessao):
        materia = MateriaLegislativa.objects.filter(
            id=votacao.materia.id).first()
        dic_votacao = {}
        dic_votacao["tipo_materia"] = materia.tipo.sigla + \
            ' - ' + materia.tipo.descricao
        dic_votacao["num_ordem"] = votacao.numero_ordem
        dic_votacao["id_materia"] = str(
            materia.numero) + "/" + str(materia.ano)
        dic_votacao["txt_ementa"] = materia.ementa
        dic_votacao["ordem_observacao"] = votacao.observacao

        dic_votacao["des_numeracao"] = ' '

        numeracao = Numeracao.objects.filter(materia=votacao.materia).first()
        if numeracao:
            dic_votacao["des_numeracao"] = str(
                numeracao.numero_materia) + '/' + str(numeracao.ano_materia)

        turno, tramitacao = get_turno(materia)
        dic_votacao["des_turno"] = turno
        dic_votacao["des_situacao"] = tramitacao

        dic_votacao["nom_autor"] = ''
        autoria = materia.autoria_set.all()
        dic_votacao['num_autores'] = 'Autores' if len(autoria) > 1 else 'Autor'
        if autoria:
            for a in autoria:
                if a.autor.nome:
                    dic_votacao['nom_autor'] += a.autor.nome + ', '
            dic_votacao['nom_autor'] = dic_votacao['nom_autor'][:-2]
        else:
            dic_votacao["nom_autor"] = 'Desconhecido'

        lst_votacao.append(dic_votacao)

    expediente = ExpedienteSessao.objects.filter(
        sessao_plenaria_id=sessao.id)
    expedientes = []
    for e in expediente:
        tipo = e.tipo
        conteudo = re.sub(
            '&nbsp;', ' ', strip_tags(e.conteudo.replace('<br/>', '\n')))
        ex = {'tipo': tipo, 'conteudo': conteudo}
        expedientes.append(ex)

    return (lst_expediente_materia,
            lst_votacao,
            inf_basicas_dic,
            expedientes)

def make_pdf(base_url,main_template,header_template,main_css='',header_css=''):
    html = HTML(base_url=base_url, string=main_template)
    main_doc = html.render(stylesheets=[])

    def get_page_body(boxes):
        for box in boxes:
            if box.element_tag == 'body':
                return box
            return get_page_body(box.all_children())

    # Template of header
    html = HTML(base_url=base_url,string=header_template)
    header = html.render(stylesheets=[CSS(string='@page {size:A4; margin:1cm;}')])

    header_page = header.pages[0]
    header_body = get_page_body(header_page._page_box.all_children())
    header_body = header_body.copy_with_children(header_body.all_children())

    for page in main_doc.pages:
        page_body = get_page_body(page._page_box.all_children())
        page_body.children += header_body.all_children()
       
    pdf_file = main_doc.write_pdf()

    return pdf_file


def resumo_ata_pdf(request,pk):
    base_url = request.build_absolute_uri()
    casa = CasaLegislativa.objects.first()
    rodape = ' '.join(get_rodape(casa))
   
    sessao_plenaria = SessaoPlenaria.objects.get(pk=pk)
    
    context = {}
    context.update(get_identificacao_basica(sessao_plenaria))
    context.update(get_mesa_diretora(sessao_plenaria))
    context.update(get_presenca_sessao(sessao_plenaria))
    context.update(get_expedientes(sessao_plenaria))
    context.update(get_materias_expediente(sessao_plenaria))
    context.update(get_oradores_expediente(sessao_plenaria))
    context.update(get_presenca_ordem_do_dia(sessao_plenaria))
    context.update(get_materias_ordem_do_dia(sessao_plenaria))
    context.update(get_oradores_ordemdia(sessao_plenaria))
    context.update(get_oradores_explicacoes_pessoais(sessao_plenaria))
    context.update(get_ocorrencias_da_sessao(sessao_plenaria))
    context.update(get_assinaturas(sessao_plenaria))
    context.update({'object': sessao_plenaria})
    context.update({'data': dt.today().strftime('%d/%m/%Y')})
    context.update({'rodape': rodape})
    header_context = {"casa": casa, 'logotipo':casa.logotipo, 'MEDIA_URL': MEDIA_URL}

    html_template = render_to_string('relatorios/relatorio_ata.html', context)
    html_header = render_to_string('relatorios/header_ata.html', header_context)

    pdf_file = make_pdf(base_url=base_url,main_template=html_template,header_template=html_header)
    
    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response


def relatorio_doc_administrativos(request, context):
    base_url = request.build_absolute_uri()
    casa = CasaLegislativa.objects.first()
    rodape = ' '.join(get_rodape(casa))

    context.update({'data': dt.today().strftime('%d/%m/%Y')})
    context.update({'rodape': rodape})

    header_context = {"casa": casa, 'logotipo':casa.logotipo, 'MEDIA_URL': MEDIA_URL}

    html_template = render_to_string('relatorios/relatorio_doc_administrativos.html', context)
    html_header = render_to_string('relatorios/header_ata.html', header_context)

    pdf_file = make_pdf(base_url=base_url,main_template=html_template,header_template=html_header)
    
    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response

def relatorio_sessao_plenaria_pdf(request, pk):  
    base_url=request.build_absolute_uri()
    logger = logging.getLogger(__name__)
    username = request.user.username
    casa = CasaLegislativa.objects.first()
    if not casa:
        raise Http404

    rodape = get_rodape(casa)
    rodape = ' '.join(rodape)

    try:
        logger.debug("user=" + username +
                     ". Tentando obter SessaoPlenaria com id={}.".format(pk))
        sessao = SessaoPlenaria.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        logger.error("user=" + username +
                     ". Essa SessaoPlenaria não existe (pk={}). ".format(pk) + str(e))
        raise Http404('Essa página não existe')

    (inf_basicas_dic,
        cont_mult_dic,
        lst_mesa,
        lst_presenca_sessao,
        lst_ausencia_sessao,
        lst_expedientes,
        lst_expediente_materia,
        lst_expediente_materia_vot_nom,
        lst_oradores_expediente,
        lst_presenca_ordem_dia,
        lst_votacao,
        lst_votacao_vot_nom,
        lst_oradores_ordemdia,
        lst_oradores,
        lst_ocorrencias) = get_sessao_plenaria(sessao, casa)

    html_template = render_to_string('relatorios/relatorio_sessao_plenaria.html',
    {       
        "inf_basicas_dic":inf_basicas_dic,
        "lst_mesa":lst_mesa,
        "lst_presenca_sessao":lst_presenca_sessao,
        "lst_ausencia_sessao":lst_ausencia_sessao,
        "lst_expedientes":lst_expedientes,
        "lst_expediente_materia":lst_expediente_materia,
        "lst_oradores_expediente":lst_oradores_expediente,
        "lst_presenca_ordem_dia":lst_presenca_ordem_dia,
        "lst_votacao":lst_votacao,
        "lst_oradores":lst_oradores,
        "lst_ocorrencias":lst_ocorrencias,
        "rodape":rodape,
        "data": dt.today().strftime('%d/%m/%Y')
    })

    info = "Resumo da {}ª Reunião {} \
                da {}ª Sessão Legislativa da {} \
                Legislatura".format(inf_basicas_dic['num_sessao_plen'],
                                        inf_basicas_dic['nom_sessao'],
                                        inf_basicas_dic['num_sessao_leg'],
                                        inf_basicas_dic['num_legislatura']
                                    )

    html_header = render_to_string('relatorios/header_ata.html',{"casa":casa,
                                                                "MEDIA_URL": MEDIA_URL,
                                                                "logotipo": casa.logotipo,  
                                                                "info":info})

    pdf_file = make_pdf(base_url=base_url, main_template=html_template, header_template=html_header)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response

