from datetime import datetime as dt
import html
import logging
import re
import tempfile

from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import ugettext_lazy as _
import unidecode
from weasyprint import HTML, CSS

from sapl.base.models import Autor, CasaLegislativa, AppConfig as SaplAppConfig
from sapl.comissoes.models import Comissao
from sapl.materia.models import (Autoria, MateriaLegislativa, Numeracao,
                                 Tramitacao, UnidadeTramitacao, ConfigEtiquetaMateriaLegislativa)
from sapl.parlamentares.models import CargoMesa, Filiacao, Parlamentar
from sapl.protocoloadm.models import (DocumentoAdministrativo, Protocolo,
                                      TramitacaoAdministrativo)
from sapl.sessao.models import (ExpedienteMateria, ExpedienteSessao,
                                IntegranteMesa, JustificativaAusencia,
                                Orador, OradorExpediente,
                                OrdemDia, PresencaOrdemDia, SessaoPlenaria,
                                SessaoPlenariaPresenca, OcorrenciaSessao,
                                RegistroVotacao, VotoParlamentar, OradorOrdemDia,
                                ConsideracoesFinais, TipoExpediente, ResumoOrdenacao)
from sapl.sessao.views import (get_identificacao_basica, get_mesa_diretora,
                               get_presenca_sessao, get_expedientes,
                               get_materias_expediente, get_oradores_expediente,
                               get_presenca_ordem_do_dia, get_materias_ordem_do_dia,
                               get_oradores_ordemdia,
                               get_oradores_explicacoes_pessoais, get_consideracoes_finais,
                               get_ocorrencias_da_sessao, get_assinaturas,
                               get_correspondencias)
from sapl.settings import MEDIA_URL
from sapl.settings import STATIC_ROOT
from sapl.utils import LISTA_DE_UFS, TrocaTag, filiacao_data, create_barcode

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
            '-data_tramitacao', '-id')

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


def is_empty(value):
    if not value:
        return True

    txt = re.sub(r'\s+|<br.*/>|\n|&nbsp;', '', value)

    return True if not txt.strip() else False


def get_sessao_plenaria(sessao, casa, user):
    inf_basicas_dic = {
        "num_sessao_plen": str(sessao.numero),
        "nom_sessao": sessao.tipo.nome,
        "num_legislatura": str(sessao.legislatura),
        "num_sessao_leg": sessao.sessao_legislativa.numero,
        "dat_inicio_sessao": sessao.data_inicio.strftime("%d/%m/%Y"),
        "hr_inicio_sessao": sessao.hora_inicio,
        "dat_fim_sessao": sessao.data_fim.strftime("%d/%m/%Y") if sessao.data_fim else '',
        "hr_fim_sessao": sessao.hora_fim,
        "nom_camara": casa.nome
    }

    if sessao.tipo.nome == 'Solene':
        inf_basicas_dic["tema_solene"] = sessao.tema_solene

    # Conteudo multimidia
    cont_mult_dic = {
        "multimidia_audio": str(sessao.url_audio) if sessao.url_audio else "Indisponível",
        "multimidia_video": str(sessao.url_video) if sessao.url_video else "Indisponível"
    }

    # Lista da composicao da mesa diretora
    lst_mesa = []
    for composicao in IntegranteMesa.objects.select_related('parlamentar', 'cargo') \
            .filter(sessao_plenaria=sessao) \
            .order_by('cargo_id'):
        partido_sigla = Filiacao.objects.filter(
            parlamentar=composicao.parlamentar).first()
        sigla = '' if not partido_sigla else partido_sigla.partido.sigla
        lst_mesa.append({
            'nom_parlamentar': composicao.parlamentar.nome_parlamentar,
            'sgl_partido': sigla,
            'des_cargo': composicao.cargo.descricao
        })

    # Lista de presença na sessão
    lst_presenca_sessao = []
    presenca = SessaoPlenariaPresenca.objects.filter(
        sessao_plenaria=sessao).order_by('parlamentar__nome_parlamentar')
    for parlamentar in [p.parlamentar for p in presenca]:
        lst_presenca_sessao.append({
            "nom_parlamentar": parlamentar.nome_parlamentar,
            "sgl_partido": filiacao_data(parlamentar, sessao.data_inicio)
        })

    # Lista de ausencias na sessão
    lst_ausencia_sessao = []
    ausencia = JustificativaAusencia.objects.filter(
        sessao_plenaria=sessao).order_by('parlamentar__nome_parlamentar')
    for ausente in ausencia:
        lst_ausencia_sessao.append({
            "parlamentar": ausente.parlamentar,
            "justificativa": ausente.tipo_ausencia,
            "tipo": "Matéria" if ausente.ausencia == 1 else "Sessão"
        })

    # Exibe as Correspondencias
    lst_correspondencias = []
    qs = sessao.correspondencia_set.all()
    is_anon = user.is_anonymous
    is_ostensivo = SaplAppConfig.attr('documentos_administrativos') == 'O'
    if is_anon and not is_ostensivo:
        qs = qs.none()
    elif is_anon:
        qs = qs.filter(documento__restrito=False)
    for c in qs:
        d = c.documento
        lst_correspondencias.append(
            {
                'id': d.id,
                'tipo': c.get_tipo_display(),
                'epigrafe': d.epigrafe,
                'data': d.data.strftime('%d/%m/%Y'),
                'interessado': d.interessado,
                'assunto': d.assunto,
                'restrito': d.restrito,
                'is_ostensivo': is_ostensivo
            }
        )

    # Exibe os Expedientes
    lst_expedientes = []
    expedientes = ExpedienteSessao.objects.filter(
        sessao_plenaria=sessao).order_by('tipo__nome')
    for e in expedientes:
        conteudo = e.conteudo
        if not is_empty(conteudo):
            # unescape HTML codes
            # https://github.com/interlegis/sapl/issues/1046
            conteudo = re.sub('style=".*?"', '', conteudo)
            conteudo = re.sub('class=".*?"', '', conteudo)
            # OSTicket Ticket #796450
            conteudo = re.sub('align=".*?"', '', conteudo)
            conteudo = re.sub('<p\s+>', '<p>', conteudo)
            # OSTicket Ticket #796450
            conteudo = re.sub('<br\s+/>', '<br/>', conteudo)
            conteudo = html.unescape(conteudo)

            # escape special character '&'
            #   https://github.com/interlegis/sapl/issues/1009
            conteudo = conteudo.replace('&', '&amp;')

            # https://github.com/interlegis/sapl/issues/2386
            conteudo = remove_html_comments(conteudo)

            dic_expedientes = {
                "nom_expediente": e.tipo.nome,
                "txt_expediente": conteudo
            }

            lst_expedientes.append(dic_expedientes)

    # Lista das matérias do Expediente, incluindo o resultado das votacoes
    lst_expediente_materia = []
    for expediente_materia in ExpedienteMateria.objects.select_related("materia").filter(sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = expediente_materia.materia
        materia_em_tramitacao = materia.materiaemtramitacao_set.first()

        dic_expediente_materia = {
            "num_ordem": expediente_materia.numero_ordem,
            "id_materia": f"{materia.tipo.sigla} {materia.tipo.descricao} {str(materia.numero)}/{str(materia.ano)}",
            "des_numeracao": ' ',
            "des_turno": get_turno(materia)[0],
            "situacao": materia_em_tramitacao.tramitacao.status if materia_em_tramitacao else _("Não informada"),
            "txt_ementa": str(materia.ementa),
            "materia_observacao": materia.observacao,
            "ordem_observacao": expediente_materia.observacao,
            "nom_resultado": '',
            "nom_autor": '',
            "votacao_observacao": ' '
        }

        numeracao = Numeracao.objects.filter(
            materia=expediente_materia.materia).first()
        if numeracao:
            dic_expediente_materia["des_numeracao"] = (
                    str(numeracao.numero_materia) + '/' + str(numeracao.ano_materia))

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

        rv = expediente_materia.registrovotacao_set.filter(
            materia=expediente_materia.materia).first()
        rp = expediente_materia.retiradapauta_set.filter(
            materia=expediente_materia.materia).first()
        rl = expediente_materia.registroleitura_set.filter(
            materia=expediente_materia.materia).first()
        if rv:
            resultado = rv.tipo_resultado_votacao.nome
            resultado_observacao = rv.observacao
        elif rp:
            resultado = rp.tipo_de_retirada.descricao
            resultado_observacao = rp.observacao
        elif rl:
            resultado = _('Matéria lida')
            resultado_observacao = rl.observacao
        else:
            resultado = _('Matéria não lida') \
                if expediente_materia.tipo_votacao == 4 \
                else _('Matéria não votada')
            resultado_observacao = _(' ')

        dic_expediente_materia.update({
            "nom_resultado": resultado,
            "votacao_observacao": resultado_observacao
        })

        lst_expediente_materia.append(dic_expediente_materia)

    # Lista dos votos nominais das matérias do Expediente
    lst_expediente_materia_vot_nom = []

    materias_expediente_votacao_nominal = ExpedienteMateria.objects.filter(sessao_plenaria=sessao, tipo_votacao=2) \
        .order_by('-materia')

    for mevn in materias_expediente_votacao_nominal:
        votos_materia = []
        titulo_materia = mevn.materia
        registro = RegistroVotacao.objects.filter(expediente=mevn)

        if registro:
            for vp in VotoParlamentar.objects.filter(votacao__in=registro).order_by('parlamentar'):
                votos_materia.append(vp)

        lst_expediente_materia_vot_nom.append({
            "titulo": titulo_materia,
            "votos": votos_materia
        })

    # Lista dos oradores do Expediente
    lst_oradores_expediente = []
    for orador_expediente in OradorExpediente.objects.filter(sessao_plenaria=sessao).order_by('numero_ordem'):
        parlamentar = Parlamentar.objects.get(
            id=orador_expediente.parlamentar.id)
        partido_sigla = Filiacao.objects.filter(
            parlamentar=parlamentar).first()
        lst_oradores_expediente.append({
            "num_ordem": orador_expediente.numero_ordem,
            "nom_parlamentar": parlamentar.nome_parlamentar,
            "observacao": orador_expediente.observacao,
            "sgl_partido": "" if not partido_sigla else partido_sigla.partido.sigla
        })

    # Lista presença na ordem do dia
    lst_presenca_ordem_dia = []
    presenca_ordem_dia = PresencaOrdemDia.objects.filter(sessao_plenaria=sessao) \
        .order_by('parlamentar__nome_parlamentar')
    for parlamentar in [p.parlamentar for p in presenca_ordem_dia]:
        lst_presenca_ordem_dia.append({
            "nom_parlamentar": parlamentar.nome_parlamentar,
            "sgl_partido": filiacao_data(parlamentar, sessao.data_inicio)
        })

    # Lista das matérias da Ordem do Dia, incluindo o resultado das votacoes
    lst_votacao = []
    for votacao in OrdemDia.objects.filter(sessao_plenaria=sessao):
        # seleciona os detalhes de uma matéria
        materia = votacao.materia
        dic_votacao = {
            "nom_resultado": '',
            "num_ordem": votacao.numero_ordem,
            "id_materia": (
                    materia.tipo.sigla + ' ' +
                    materia.tipo.descricao + ' ' +
                    str(materia.numero) + '/' +
                    str(materia.ano)),
            "des_numeracao": ' '
        }

        numeracao = materia.numeracao_set.first()
        if numeracao:
            dic_votacao["des_numeracao"] = (
                    str(numeracao.numero_materia) + '/' + str(numeracao.ano_materia))

        materia_em_tramitacao = materia.materiaemtramitacao_set.first()
        dic_votacao.update({
            "des_turno": get_turno(materia)[0],
            # https://github.com/interlegis/sapl/issues/1009
            "txt_ementa": html.unescape(materia.ementa),
            "materia_observacao": materia.observacao,
            "ordem_observacao": html.unescape(votacao.observacao),
            "nom_autor": '',
            "situacao": materia_em_tramitacao.tramitacao.status if materia_em_tramitacao else _("Não informada")
        })

        autoria = materia.autoria_set.all()
        dic_votacao['num_autores'] = 'Autores' if len(autoria) > 1 else 'Autor'
        if autoria:
            for a in autoria:
                if a.autor.nome:
                    dic_votacao['nom_autor'] += a.autor.nome + ', '
            dic_votacao['nom_autor'] = dic_votacao['nom_autor'][:-2]
        else:
            dic_votacao["nom_autor"] = 'Desconhecido'

        rv = votacao.registrovotacao_set.filter(
            materia=votacao.materia).first()
        rp = votacao.retiradapauta_set.filter(
            materia=votacao.materia).first()
        rl = votacao.registroleitura_set.filter(
            materia=votacao.materia).first()
        if rv:
            resultado = rv.tipo_resultado_votacao.nome
            resultado_observacao = rv.observacao
        elif rp:
            resultado = rp.tipo_de_retirada.descricao
            resultado_observacao = rp.observacao
        elif rl:
            resultado = _('Matéria lida')
            resultado_observacao = rl.observacao
        else:
            resultado = _('Matéria não lida') if \
                votacao.tipo_votacao == 4 else _('Matéria não votada')
            resultado_observacao = _(' ')

        dic_votacao.update({
            "nom_resultado": resultado,
            "votacao_observacao": resultado_observacao
        })

        lst_votacao.append(dic_votacao)

    # Lista dos votos nominais das matérias da Ordem do Dia
    lst_votacao_vot_nom = []

    materias_ordem_dia_votacao_nominal = OrdemDia.objects.filter(sessao_plenaria=sessao, tipo_votacao=2) \
        .order_by('-materia')

    for modvn in materias_ordem_dia_votacao_nominal:
        votos_materia_od = []
        t_materia = modvn.materia
        registro_od = RegistroVotacao.objects.filter(ordem=modvn)

        if registro_od:
            for vp_od in VotoParlamentar.objects.filter(votacao__in=registro_od).order_by('parlamentar'):
                votos_materia_od.append(vp_od)

        lst_votacao_vot_nom.append({
            "titulo": t_materia,
            "votos": votos_materia_od
        })

    # Lista dos oradores da Ordem do Dia
    lst_oradores_ordemdia = []

    oradores_ordem_dia = OradorOrdemDia.objects.filter(
        sessao_plenaria=sessao).order_by('numero_ordem')

    for orador_ordemdia in oradores_ordem_dia:
        parlamentar_orador = Parlamentar.objects.get(
            id=orador_ordemdia.parlamentar.id)
        sigla_partido = Filiacao.objects.filter(
            parlamentar=parlamentar_orador).first()

        lst_oradores_ordemdia.append({
            "num_ordem": orador_ordemdia.numero_ordem,
            "nome_parlamentar": parlamentar_orador.nome_parlamentar,
            "observacao": orador_ordemdia.observacao,
            "sigla": "" if not sigla_partido else sigla_partido.partido.sigla
        })

    # Lista dos oradores nas Explicações Pessoais
    lst_oradores = []
    for orador in Orador.objects.select_related('parlamentar').filter(sessao_plenaria=sessao).order_by('numero_ordem'):
        parlamentar = orador.parlamentar
        partido_sigla = orador.parlamentar.filiacao_set.select_related(
            'partido', 'parlamentar').first()
        lst_oradores.append({
            "num_ordem": orador.numero_ordem,
            "nom_parlamentar": parlamentar.nome_parlamentar,
            "observacao": orador.observacao,
            "sgl_partido": "" if not partido_sigla else partido_sigla.partido.sigla
        })

    # Ocorrências da Sessão
    lst_ocorrencias = []
    ocorrencias = OcorrenciaSessao.objects.filter(sessao_plenaria=sessao)
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

    # Ocorrências da Sessão
    lst_consideracoes = []
    consideracoes = ConsideracoesFinais.objects.filter(sessao_plenaria=sessao)

    for c in consideracoes:
        conteudo = c.conteudo

        # unescape HTML codes
        # https://github.com/interlegis/sapl/issues/1046
        conteudo = re.sub('style=".*?"', '', conteudo)
        conteudo = html.unescape(conteudo)

        # escape special character '&'
        #   https://github.com/interlegis/sapl/issues/1009
        conteudo = conteudo.replace('&', '&amp;')

        c.conteudo = conteudo

        lst_consideracoes.append(c)

    return (inf_basicas_dic,
            cont_mult_dic,
            lst_mesa,
            lst_presenca_sessao,
            lst_ausencia_sessao,
            lst_correspondencias,
            lst_expedientes,
            lst_expediente_materia,
            lst_expediente_materia_vot_nom,
            lst_oradores_expediente,
            lst_presenca_ordem_dia,
            lst_votacao,
            lst_votacao_vot_nom,
            lst_oradores_ordemdia,
            lst_oradores,
            lst_ocorrencias,
            lst_consideracoes)


def get_turno(materia):
    descricao_turno = ''
    descricao_tramitacao = ''
    tramitacoes = materia.tramitacao_set.order_by(
        '-data_tramitacao', '-id').all()
    tramitacoes_turno = tramitacoes.exclude(turno="")

    if tramitacoes:
        if tramitacoes_turno:
            for t in Tramitacao.TURNO_CHOICES:
                if t[0] == tramitacoes_turno.first().turno:
                    descricao_turno = str(t[1])
                    break
        descricao_tramitacao = tramitacoes.first(
        ).status.descricao if tramitacoes.first().status else 'Não informada'
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
     lst_correspondencias,
     lst_expedientes,
     lst_expediente_materia,
     lst_expediente_materia_vot_nom,
     lst_oradores_expediente,
     lst_presenca_ordem_dia,
     lst_votacao,
     lst_votacao_vot_nom,
     lst_oradores_ordemdia,
     lst_oradores,
     lst_ocorrencias,
     lst_consideracoes) = get_sessao_plenaria(sessao, casa, request.user)

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
        lst_correspondencias,
        lst_expedientes,
        lst_expediente_materia,
        lst_expediente_materia_vot_nom,
        lst_oradores_expediente,
        lst_presenca_ordem_dia,
        lst_votacao,
        lst_votacao_vot_nom,
        lst_oradores_ordemdia,
        lst_oradores,
        lst_ocorrencias,
        lst_consideracoes)

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

    m = MateriaLegislativa.objects.filter(numero_protocolo=nro, ano=ano)

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
        dic_expediente_materia["materia_observacao"] = materia.observacao

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
        conteudo = e.conteudo
        if not is_empty(conteudo):
            # unescape HTML codes
            # https://github.com/interlegis/sapl/issues/1046
            conteudo = re.sub('style=".*?"', '', conteudo)
            conteudo = re.sub('class=".*?"', '', conteudo)
            # OSTicket Ticket #796450
            conteudo = re.sub('align=".*?"', '', conteudo)
            conteudo = re.sub('<p\s+>', '<p>', conteudo)
            # OSTicket Ticket #796450
            conteudo = re.sub('<br\s+/>', '<br/>', conteudo)
            conteudo = html.unescape(conteudo)

            # escape special character '&'
            #   https://github.com/interlegis/sapl/issues/1009
            conteudo = conteudo.replace('&', '&amp;')

            # https://github.com/interlegis/sapl/issues/2386
            conteudo = remove_html_comments(conteudo)
        ex = {'tipo': tipo, 'conteudo': conteudo}
        expedientes.append(ex)

    return (lst_expediente_materia,
            lst_votacao,
            inf_basicas_dic,
            expedientes)


def make_pdf(base_url, main_template, header_template, main_css='', header_css=''):
    html = HTML(base_url=base_url, string=main_template)
    main_doc = html.render(stylesheets=[])

    def get_page_body(boxes):
        for box in boxes:
            if box.element_tag == 'body':
                return box
            return get_page_body(box.all_children())

    # Template of header
    html = HTML(base_url=base_url, string=header_template)
    header = html.render(
        stylesheets=[CSS(string='@page {size:A4; margin:1cm;}')])

    header_page = header.pages[0]
    header_body = get_page_body(header_page._page_box.all_children())
    header_body = header_body.copy_with_children(header_body.all_children())

    for page in main_doc.pages:
        page_body = get_page_body(page._page_box.all_children())
        page_body.children += header_body.all_children()

    pdf_file = main_doc.write_pdf()

    return pdf_file


def resumo_ata_pdf(request, pk):
    base_url = request.build_absolute_uri()
    casa = CasaLegislativa.objects.first()
    rodape = ' '.join(get_rodape(casa))

    sessao_plenaria = SessaoPlenaria.objects.get(pk=pk)

    context = {}
    context.update(get_identificacao_basica(sessao_plenaria))
    context.update(get_mesa_diretora(sessao_plenaria))
    context.update(get_presenca_sessao(sessao_plenaria))
    context.update(get_correspondencias(sessao_plenaria, request.user))
    context.update(get_expedientes(sessao_plenaria))
    context.update(get_materias_expediente(sessao_plenaria))
    context.update(get_oradores_expediente(sessao_plenaria))
    context.update(get_presenca_ordem_do_dia(sessao_plenaria))
    context.update(get_materias_ordem_do_dia(sessao_plenaria))
    context.update(get_oradores_ordemdia(sessao_plenaria))
    context.update(get_ocorrencias_da_sessao(sessao_plenaria))
    context.update(get_consideracoes_finais(sessao_plenaria))
    context.update(get_oradores_explicacoes_pessoais(sessao_plenaria))
    context.update(get_assinaturas(sessao_plenaria))
    context.update({'object': sessao_plenaria})
    context.update({'data': dt.today().strftime('%d/%m/%Y')})
    context.update({'rodape': rodape})
    header_context = {"casa": casa,
                      'logotipo': casa.logotipo, 'MEDIA_URL': MEDIA_URL}

    html_template = render_to_string('relatorios/relatorio_ata.html', context)
    html_header = render_to_string(
        'relatorios/header_ata.html', header_context)

    pdf_file = make_pdf(
        base_url=base_url, main_template=html_template, header_template=html_header)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response


def cria_relatorio(request, context, html_string, header_info=""):
    base_url = request.build_absolute_uri()
    casa = CasaLegislativa.objects.first()
    rodape = ' '.join(get_rodape(casa))

    context.update({'data': dt.today().strftime('%d/%m/%Y')})
    context.update({'rodape': rodape})

    header_context = {"casa": casa, 'logotipo': casa.logotipo,
                      'MEDIA_URL': MEDIA_URL, 'info': header_info}

    html_template = render_to_string(html_string, context)
    html_header = render_to_string(
        'relatorios/header_ata.html', header_context)

    pdf_file = make_pdf(
        base_url=base_url, main_template=html_template, header_template=html_header)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response


def relatorio_doc_administrativos(request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_doc_administrativos.html')


def relatorio_materia_em_tramitacao(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_materias_em_tramitacao.html')


def relatorio_materia_por_autor(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_materias_por_autor.html')


def relatorio_materia_por_ano_autor(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_materias_por_ano_autor.html')


def relatorio_presenca_sessao(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_presenca_sessao.html')


def relatorio_atas(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_atas.html')


def relatorio_historico_tramitacao(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_historico_tramitacao.html')


def relatorio_fim_prazo_tramitacao(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_fim_prazo_tramitacao.html')


def relatorio_reuniao(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_reuniao.html')


def relatorio_audiencia(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_audiencia.html')


def relatorio_normas_mes(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_normas_mes.html')


def relatorio_normas_vigencia(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_normas_vigencia.html')


def relatorio_historico_tramitacao_adm(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_historico_tramitacao_adm.html')


def relatorio_estatisticas_acesso_normas(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_estatisticas_acesso_normas.html')


def relatorio_documento_acessorio(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_documento_acessorio.html')


def relatorio_normas_por_autor(obj, request, context):
    return cria_relatorio(request, context, 'relatorios/relatorio_normas_por_autor.html')


def relatorio_pauta_sessao_weasy(obj, request, context):
    sessao = context['object']
    info = f"Pauta da {sessao} ({sessao.legislatura.data_inicio.year} - {sessao.legislatura.data_fim.year}) Legislatura"
    return cria_relatorio(request, context, 'relatorios/relatorio_pauta_sessao.html', info)


def relatorio_sessao_plenaria_pdf(request, pk):
    base_url = request.build_absolute_uri()
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
     lst_correspondencias,
     lst_expedientes,
     lst_expediente_materia,
     lst_expediente_materia_vot_nom,
     lst_oradores_expediente,
     lst_presenca_ordem_dia,
     lst_votacao,
     lst_votacao_vot_nom,
     lst_oradores_ordemdia,
     lst_oradores,
     lst_ocorrencias,
     lst_consideracoes) = get_sessao_plenaria(sessao, casa, request.user)

    dict_ord_template = {
        'cont_mult': 'conteudo_multimidia.html',
        'correspondencia': 'correspondencias.html',
        'exp': 'expedientes.html',
        'id_basica': 'identificacao_basica.html',
        'lista_p': 'lista_presenca_sessao.html',
        'lista_p_o_d': 'lista_presenca_ordemdia.html',
        'mat_exp': 'materias_expediente.html',
        'v_n_mat_exp': 'votos_nominais_expediente.html',
        'mat_o_d': 'materias_ordemdia.html',
        'v_n_mat_o_d': 'votos_nominais_ordemdia.html',
        'mesa_d': 'mesa_diretora.html',
        'oradores_exped': 'oradores_expediente.html',
        'oradores_o_d': 'oradores_ordemdia.html',
        'oradores_expli': 'oradores_explicacoes.html',
        'ocorr_sessao': 'ocorrencias_da_sessao.html',
        'cons_finais': 'consideracoes_finais.html'
    }

    context = {
        "inf_basicas_dic": inf_basicas_dic,
        "cont_mult_dic": cont_mult_dic,
        "lst_mesa": lst_mesa,
        "lst_expediente_materia_vot_nom": lst_expediente_materia_vot_nom,
        "lst_presenca_sessao": lst_presenca_sessao,
        "lst_ausencia_sessao": lst_ausencia_sessao,
        "lst_correspondencias": lst_correspondencias,
        "lst_expedientes": lst_expedientes,
        "lst_expediente_materia": lst_expediente_materia,
        "lst_oradores_expediente": lst_oradores_expediente,
        "lst_presenca_ordem_dia": lst_presenca_ordem_dia,
        "lst_votacao": lst_votacao,
        "lst_oradores_ordemdia": lst_oradores_ordemdia,
        "lst_votacao_vot_nom": lst_votacao_vot_nom,
        "lst_oradores": lst_oradores,
        "lst_ocorrencias": lst_ocorrencias,
        "lst_consideracoes": lst_consideracoes,
        "rodape": rodape,
        "data": dt.today().strftime('%d/%m/%Y')
    }

    ordenacao = ResumoOrdenacao.objects.get_or_create()[0]
    try:
        context.update({
            'primeiro_ordenacao': dict_ord_template[ordenacao.primeiro],
            'segundo_ordenacao': dict_ord_template[ordenacao.segundo],
            'terceiro_ordenacao': dict_ord_template[ordenacao.terceiro],
            'quarto_ordenacao': dict_ord_template[ordenacao.quarto],
            'quinto_ordenacao': dict_ord_template[ordenacao.quinto],
            'sexto_ordenacao': dict_ord_template[ordenacao.sexto],
            'setimo_ordenacao': dict_ord_template[ordenacao.setimo],
            'oitavo_ordenacao': dict_ord_template[ordenacao.oitavo],
            'nono_ordenacao': dict_ord_template[ordenacao.nono],
            'decimo_ordenacao': dict_ord_template[ordenacao.decimo],
            'decimo_primeiro_ordenacao': dict_ord_template[ordenacao.decimo_primeiro],
            'decimo_segundo_ordenacao': dict_ord_template[ordenacao.decimo_segundo],
            'decimo_terceiro_ordenacao': dict_ord_template[ordenacao.decimo_terceiro],
            'decimo_quarto_ordenacao': dict_ord_template[ordenacao.decimo_quarto],
            'decimo_quinto_ordenacao': dict_ord_template[ordenacao.decimo_quinto],
            'decimo_sexto_ordenacao': dict_ord_template[ordenacao.decimo_sexto]
        })
    except KeyError as e:
        # self.logger.error("KeyError: " + str(e) + ". Erro ao tentar utilizar "
        #                                           "configuração de ordenação. Utilizando ordenação padrão.")
        context.update({
            'primeiro_ordenacao': 'identificacao_basica.html',
            'segundo_ordenacao': 'conteudo_multimidia.html',
            'terceiro_ordenacao': 'mesa_diretora.html',
            'quarto_ordenacao': 'lista_presenca_sessao.html',
            'quinto_ordenacao': 'correspondencias.html',
            'sexto_ordenacao': 'expedientes.html',
            'setimo_ordenacao': 'materias_expediente.html',
            'oitavo_ordenacao': 'votos_nominais_expediente.html',
            'nono_ordenacao': 'oradores_expediente.html',
            'decimo_ordenacao': 'lista_presenca_ordemdia.html',
            'decimo_primeiro_ordenacao': 'materias_ordemdia.html',
            'decimo_segundo_ordenacao': 'votos_nominais_ordemdia.html',
            'decimo_terceiro_ordenacao': 'oradores_ordemdia.html',
            'decimo_quarto_ordenacao': 'oradores_explicacoes.html',
            'decimo_quinto_ordenacao': 'ocorrencias_da_sessao.html',
            'decimo_sexto_ordenacao': 'consideracoes_finais.html'
        })

    html_template = render_to_string(
        'relatorios/relatorio_sessao_plenaria.html', context)

    info = "Resumo da {}ª Reunião {} \
                da {}ª Sessão Legislativa da {} \
                Legislatura".format(inf_basicas_dic['num_sessao_plen'],
                                    inf_basicas_dic['nom_sessao'],
                                    inf_basicas_dic['num_sessao_leg'],
                                    inf_basicas_dic['num_legislatura']
                                    )

    html_header = render_to_string('relatorios/header_ata.html', {"casa": casa,
                                                                  "MEDIA_URL": MEDIA_URL,
                                                                  "logotipo": casa.logotipo,
                                                                  "info": info})

    pdf_file = make_pdf(
        base_url=base_url, main_template=html_template, header_template=html_header)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response


def gera_etiqueta_ml(materia_legislativa, base_url):
    confg = ConfigEtiquetaMateriaLegislativa.objects.first()

    ml_info = unidecode.unidecode("{}/{}-{}".format(materia_legislativa.numero,
                                                    materia_legislativa.ano,
                                                    materia_legislativa.tipo.sigla))
    base64_data = create_barcode(ml_info, 100, 500)
    barcode = 'data:image/png;base64,{0}'.format(base64_data)

    max_ementa_size = 240
    ementa = materia_legislativa.ementa
    ementa = ementa if len(
        ementa) < max_ementa_size else ementa[:max_ementa_size] + "..."

    context = {
        'numero': materia_legislativa.numero,
        'ano': materia_legislativa.ano,
        'tipo': materia_legislativa.tipo,
        'data_apresentacao': materia_legislativa.data_apresentacao,
        'autores': materia_legislativa.autores.all(),
        'ementa': ementa,
        'largura': confg.largura,
        'altura': confg.largura,
        'barcode': barcode
    }

    main_template = render_to_string(
        'relatorios/etiqueta_materia_legislativa.html', context)

    html = HTML(base_url=base_url, string=main_template)
    main_doc = html.render(stylesheets=[CSS(
        string="@page {{size: {}cm {}cm;}}".format(confg.largura, confg.altura))])

    pdf_file = main_doc.write_pdf()
    return pdf_file


def etiqueta_materia_legislativa(request, pk):
    base_url = request.build_absolute_uri()
    materia_legislativa = MateriaLegislativa.objects.get(pk=pk)

    pdf_file = gera_etiqueta_ml(materia_legislativa, base_url)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=etiqueta.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response


def relatorio_materia_tramitacao(request, pk):
    base_url = request.build_absolute_uri()
    materia_legislativa = MateriaLegislativa.objects.get(pk=pk)
    tramitacoes = Tramitacao.objects.filter(materia=materia_legislativa)
    casa = CasaLegislativa.objects.first()
    rodape = ' '.join(get_rodape(casa))

    context = {}
    context.update({'object': materia_legislativa})
    context.update({'data': dt.today().strftime('%d/%m/%Y')})
    context.update({'rodape': rodape})
    header_context = {"casa": casa,
                      'logotipo': casa.logotipo, 'MEDIA_URL': MEDIA_URL}

    html_template = render_to_string('crud/list.html', context)
    html_header = render_to_string(
        'relatorios/header_ata.html', header_context)

    pdf_file = make_pdf(
        base_url=base_url, main_template=html_template, header_template=html_header)

    response = HttpResponse(content_type='application/pdf;')
    response['Content-Disposition'] = 'inline; filename=relatorio.pdf'
    response['Content-Transfer-Encoding'] = 'binary'
    response.write(pdf_file)

    return response
