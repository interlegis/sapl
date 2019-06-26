# #parameters=rodape_dic, sessao='', imagem, inf_basicas_dic, lst_mesa, lst_presenca_sessao, lst_expedientes, lst_expediente_materia, lst_oradores_expediente, lst_presenca_ordem_dia, lst_votacao, lst_oradores
"""Script para geração do PDF das sessoes plenarias
   Autor: Gustavo Lepri
   Atualizado por Luciano De Fázio - 22/03/2012
   versão: 1.0
"""
import os
import time
import logging
from django.template.defaultfilters import safe
from django.utils.html import strip_tags
from trml2pdf import parseString

from sapl.sessao.models import ResumoOrdenacao


def cabecalho(inf_basicas_dic, imagem):
    """
    """
    tmp = ''
    
    if os.path.isfile(imagem):
        tmp += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
            imagem + '"/>\n'
    tmp += '\t\t\t\t<lines>2cm 25.4cm 19cm 25.4cm</lines>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica-Bold" size="16"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="27.1cm">' + \
        str(inf_basicas_dic["nom_camara"]) + '</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="12"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="26.6cm">Sistema de Apoio ao Processo Legislativo</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica-Bold" size="12"/>\n'
    tmp += '\t\t\t\t<drawString x="4.2cm" y="25cm">Resumo da ' + str(inf_basicas_dic['num_sessao_plen']) + 'ª Reunião ' + str(inf_basicas_dic['nom_sessao']) + ' da ' + str(
        inf_basicas_dic['num_sessao_leg']) + 'ª Sessão Legislativa da </drawString>\n'
    tmp += '\t\t\t\t<drawString x="6.7cm" y="24.5cm">' + \
        str(inf_basicas_dic['num_legislatura']) + \
        ' Legislatura </drawString>\n'
    return tmp


def rodape(rodape_dic):
    tmp = ''
    tmp += '\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp += '\t\t\t\t<drawString x="2cm" y="3.3cm">' + \
        rodape_dic[2] + '</drawString>\n'
    tmp += '\t\t\t\t<drawString x="17.9cm" y="3.3cm">Página <pageNumber/></drawString>\n'
    tmp += '\t\t\t\t<drawCentredString x="10.5cm" y="2.7cm">' + \
        rodape_dic[0] + '</drawCentredString>\n'
    tmp += '\t\t\t\t<drawCentredString x="10.5cm" y="2.3cm">' + \
        rodape_dic[1] + '</drawCentredString>\n'
    return tmp


def paraStyle():
    """
    """
    tmp = ''
    tmp += '\t<stylesheet>\n'
    tmp += '\t\t<blockTableStyle id="repeater" spaceBefore="12">\n'
    tmp += '\t\t\t<lineStyle kind="OUTLINE" colorName="black" thickness="0.5"/>\n'
    tmp += '\t\t\t<lineStyle kind="GRID" colorName="gray" thickness="0.25"/>\n'
    tmp += '\t\t\t<blockFont name="Helvetica-Bold" size="8" leading="8" start="0,0" stop="-1,0"/>\n'
    tmp += '\t\t\t<blockBottomPadding length="1"/>\n'
    tmp += '\t\t\t<blockBackground colorName="silver" start="0,0" stop="-1,0"/>\n'
    tmp += '\t\t\t<lineStyle kind="LINEBELOW" colorName="black" start="0,0" stop="-1,0" thickness="0.5"/>\n'
    tmp += '\t\t\t<!--body section-->\n'
    tmp += '\t\t\t<blockFont name="Helvetica" size="8" leading="9" start="0,1" stop="-1,-1"/>\n'
    tmp += '\t\t\t<blockTopPadding length="1" start="0,1" stop="-1,-1"/>\n'
    tmp += '\t\t\t<blockAlignment value="LEFT" start="1,1" stop="-1,-1"/>\n'
    tmp += '\t\t\t<blockValign value="TOP"/>\n'
    tmp += '\t\t</blockTableStyle>\n'

    tmp += '\t\t<blockTableStyle id="votacao">\n'
    tmp += '\t\t\t<blockFont name="Helvetica" size="8" leading="9" start="0,0" stop="-1,0"/>\n'
    tmp += '\t\t\t<blockBackground colorName="silver" start="0,0" stop="3,0" />\n'
    tmp += '\t\t\t<lineStyle kind="GRID" colorName="silver" />\n'
    tmp += '\t\t\t<lineStyle kind="LINEBELOW" colorName="black" start="0,0" stop="-1,0" thickness="0.5"/>\n'
    tmp += '\t\t\t<blockValign value="TOP"/>\n'
    tmp += '\t\t</blockTableStyle>\n'

    tmp += '\t\t<blockTableStyle id="expedientes">\n'
    tmp += '\t\t\t<lineStyle kind="GRID" colorName="silver" />\n'
    tmp += '\t\t\t<blockValign value="TOP"/>\n'
    tmp += '\t\t</blockTableStyle>\n'

    tmp += '\t\t<initialize>\n'
    tmp += '\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp += '\t\t</initialize>\n'
    tmp += '\t\t<paraStyle name="style.Title" fontName="Helvetica" fontSize="11" leading="13" alignment="RIGHT"/>\n'
    tmp += '\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="12.0" textColor="gray" leading="14" spaceBefore="12" alignment="LEFT"/>\n'
    tmp += '\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="10.0" leading="10" alignment="JUSTIFY"/>\n'
    tmp += '\t\t<paraStyle name="P3" fontName="Helvetica" fontSize="9" leading="10" spaceAfter="3" alignment="LEFT"/>\n'
    tmp += '\t\t<paraStyle name="P4" fontName="Helvetica" fontSize="8" leading="9" spaceAfter="3" alignment="JUSTIFY"/>\n'
    tmp += '\t\t<paraStyle name="texto_projeto" fontName="Helvetica" fontSize="12.0" leading="12" spaceAfter="10" alignment="JUSTIFY"/>\n'
    tmp += '\t\t<paraStyle name="numOrdem" alignment="CENTER"/>\n'
    tmp += '\t</stylesheet>\n'

    return tmp


def inf_basicas(inf_basicas_dic):
    """
    """
    tmp = ""
    nom_sessao = inf_basicas_dic['nom_sessao']
    # num_sessao_plen = inf_basicas_dic["num_sessao_plen"]
    # num_sessao_leg = inf_basicas_dic["num_sessao_leg"]
    # num_legislatura = inf_basicas_dic["num_legislatura"]
    dat_inicio_sessao = inf_basicas_dic["dat_inicio_sessao"]
    hr_inicio_sessao = inf_basicas_dic["hr_inicio_sessao"]
    dat_fim_sessao = inf_basicas_dic["dat_fim_sessao"]
    hr_fim_sessao = inf_basicas_dic["hr_fim_sessao"]
    if hr_fim_sessao is None:
        hr_fim_sessao = ''

    if nom_sessao or dat_inicio_sessao or hr_inicio_sessao \
        or dat_fim_sessao or hr_fim_sessao:
        tmp += '\t\t<para style="P1">Informações Básicas</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        if nom_sessao:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>Tipo da Sessão: </b> ' + \
                nom_sessao + '</para>\n'
        if hr_inicio_sessao:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>Abertura: </b> ' + \
                dat_inicio_sessao + ' <b>- </b> ' + hr_inicio_sessao + '</para>\n'
        if dat_fim_sessao or hr_fim_sessao:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>Encerramento: </b> ' + \
                dat_fim_sessao + ' <b>- </b> ' + hr_fim_sessao + '</para>\n'
    if inf_basicas_dic.get('tema_solene'):
        tmp += '\t\t<para style="P2" spaceAfter="5"><b>Tema da Sessão Solene: </b> ' + \
                inf_basicas_dic['tema_solene'] + '</para>\n'

    return tmp


def multimidia(cont_mult_dic):
    """
    """
    tmp = ""
    
    mul_audio = cont_mult_dic['multimidia_audio']
    mul_video = cont_mult_dic['multimidia_video']

    if mul_audio or mul_video:
        tmp += '\t\t<para style="P1">Conteúdo Multimídia</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        if mul_audio:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>Audio: </b> ' + mul_audio + '</para>\n'
        if mul_video:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>Video: </b> ' + mul_video + '</para>\n'

    return tmp


def mesa(lst_mesa):
    tmp = ''
    if lst_mesa:
        tmp += '\t\t<para style="P1">Mesa Diretora</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        for mesa in lst_mesa:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>' + \
                str(mesa['des_cargo']) + ':</b> ' + str(mesa['nom_parlamentar']
                                                        ) + '/' + str(mesa['sgl_partido']) + '</para>\n'
    return tmp


def presenca(lst_presenca_sessao, lst_ausencia_sessao):
    tmp = ''
    if lst_presenca_sessao or lst_ausencia_sessao:
        if lst_ausencia_sessao:
            tmp += '\t\t<para style="P1">Lista de Presença da Sessão</para>\n'
            tmp += '\t\t<para style="P2">\n'
            tmp += '\t\t\t<font color="white"> <br/></font>\n'
            tmp += '\t\t</para>\n'
            for presenca in lst_presenca_sessao:
                tmp += '\t\t<para style="P2" spaceAfter="5">' + \
                    str(presenca['nom_parlamentar']) + '/' + \
                    str(presenca['sgl_partido']) + '</para>\n'
        if lst_ausencia_sessao:
            tmp += '\t\t<para style="P1">Justificativas de Ausência da Sessão</para>\n'
            tmp += '\t\t<para style="P2">\n'
            tmp += '\t\t\t<font color="white"> <br/></font>\n'
            tmp += '\t\t</para>\n'
            tmp += '<blockTable style="repeater" repeatRows="1">\n'
            tmp += '<tr><td >Parlamentar</td><td>Justificativa</td><td>Ausente em</td></tr>\n'
            for ausencia in lst_ausencia_sessao:
                tmp += '<tr><td>' + \
                    str(ausencia['parlamentar']) + '</td><td> ' + \
                    str(ausencia['justificativa']) + '</td><td>' + \
                    str(ausencia['tipo']) + '</td></tr>\n'
            tmp += '</blockTable>'
    return tmp


def expedientes(lst_expedientes):
    tmp = ''
    if lst_expedientes:
        tmp += '\t\t<para style="P1">Expedientes</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'
        for expediente in lst_expedientes:
            if expediente['txt_expediente']:
                tmp += '\t\t<para style="P2"><b>' + '<br/> ' + \
                    expediente['nom_expediente'] + ': </b></para>\n' + \
                    '<para style="P3">' + \
                    expediente['txt_expediente'] + '</para>\n'
                tmp += '\t\t<para style="P2">\n'
                tmp += '\t\t\t<font color="white"> </font>\n'
                tmp += '\t\t</para>\n'
    return tmp


def expediente_materia(lst_expediente_materia):
    tmp = ''
    if lst_expediente_materia:
        tmp += '\t\t<para style="P1">Matérias do Expediente</para>\n\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        tmp += '<blockTable style="repeater" repeatRows="1" colWidths="3.5cm,11.5cm,3.5cm">>\n'
        tmp += '<tr><td >Matéria</td><td>Ementa</td><td>Resultado da Votação</td></tr>\n'
        for expediente_materia in lst_expediente_materia:
            tmp += '<tr><td><para style="P3"><b>' + str(expediente_materia['num_ordem']) + '</b> - ' + expediente_materia['id_materia'] + '</para>\n' + '<para style="P3"><b>Turno: </b>' + expediente_materia[
            'des_turno'] + '</para>\n' + '<para style="P3"><b>' + expediente_materia['num_autores'] + ': </b>' + str(expediente_materia['nom_autor']) + '</para></td>\n'
            
            txt_ementa = expediente_materia['txt_ementa'].replace('&', '&amp;')
            
            # txt_ementa = dont_break_out(expediente_materia['txt_ementa'])
                    
            # if len(txt_ementa) > 800:
            #    txt_ementa = txt_ementa[:800] + "..."
            tmp += '<td><para style="P4">' + txt_ementa + '</para>' + '<para style="P4">' + expediente_materia['ordem_observacao'] + '</para></td>\n'
            tmp += '<td><para style="P3"><b>' + \
                str(expediente_materia['nom_resultado']) + \
                '</b></para>\n' + '<para style="P3">'
            if expediente_materia['votacao_observacao'] != txt_ementa:
                tmp += str(expediente_materia['votacao_observacao'])
            else:
                tmp += ' '
            tmp += '</para></td></tr>\n'

        tmp += '\t\t</blockTable>\n'
    return tmp


def expediente_materia_vot_nom(lst_expediente_materia_vot_nom):
    tmp = ''
    if lst_expediente_materia_vot_nom:
        tmp += '\t\t<para style="P1">Votações Nominais - Matérias do Expediente</para>\n\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        tmp += '<blockTable style="repeater" repeatRows="1">\n'
        tmp += '<tr><td >Matéria</td><td>Votos</td></tr>\n'
        for expediente_materia_vot_nom in lst_expediente_materia_vot_nom:
            tmp += '<tr><td><para style="P3">' + str(expediente_materia_vot_nom['titulo']) + '</para></td>'
            if expediente_materia_vot_nom['votos']:
                tmp += '<td>'
                for v in expediente_materia_vot_nom['votos']:
                    tmp += '<para style="P3"><b>' + str(v.parlamentar) + '</b> - ' + v.voto + '</para>'
                tmp += '</td>'
            else: 
                tmp += '<td><para style="P3"><b>Matéria não votada</b></para></td>'
            tmp += '</tr>\n'
        tmp += '\t\t</blockTable>\n'
    return tmp


def oradores_expediente(lst_oradores_expediente):
    tmp = ''
    if lst_oradores_expediente:
        tmp += '\t\t<para style="P1">Oradores do Expediente</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        for orador_expediente in lst_oradores_expediente:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>' + str(orador_expediente[
            'num_ordem']) + '</b> - ' + orador_expediente[
            'nom_parlamentar'] + '/' + str(orador_expediente[
            'sgl_partido']) + ' - ' + str(orador_expediente[
            'observacao']) + '</para>\n'
    return tmp


def presenca_ordem_dia(lst_presenca_ordem_dia):
    tmp = ''
    if lst_presenca_ordem_dia:
        tmp += '\t\t<para style="P1">Lista de Presença da Ordem do Dia</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        for presenca_ordem_dia in lst_presenca_ordem_dia:
            tmp += '\t\t<para style="P2" spaceAfter="5">' + \
                str(presenca_ordem_dia['nom_parlamentar']) + '/' + \
                str(presenca_ordem_dia['sgl_partido']) + '</para>\n'
    return tmp


def votacao(lst_votacao):
    tmp = ''
    if lst_votacao:
        tmp += '<para style="P1">Matérias da Ordem do Dia</para>\n\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        tmp += '<blockTable style="repeater" repeatRows="1">\n'
        tmp += '<tr><td >Matéria</td><td>Ementa</td><td>Resultado da Votação</td></tr>\n'
        for votacao in lst_votacao:
            tmp += '<tr><td><para style="P3"><b>' + str(votacao['num_ordem']) + '</b> - ' + votacao['id_materia'] + '</para>\n' + '<para style="P3"><b>Turno:</b> ' + votacao[
                'des_turno'] + '</para>\n' + '<para style="P3"><b>' + votacao['num_autores'] + ': </b>' + str(votacao['nom_autor']) + '</para></td>\n'
            txt_ementa = votacao['txt_ementa'].replace('&', '&amp;')
            if len(txt_ementa) > 1000:
                txt_ementa = txt_ementa[:1000] + "..."
            tmp += '<td><para style="P4">' + txt_ementa + '</para>' + '<para style="P4">' + votacao['ordem_observacao'] + '</para></td>\n'
            tmp += '<td><para style="P3"><b>' + \
                str(votacao['nom_resultado']) + \
                '</b></para>\n' + '<para style="P3">'
            if votacao['votacao_observacao'] != txt_ementa:
                tmp += str(votacao['votacao_observacao'])
            else:
                tmp += ' '
            tmp += '</para></td></tr>\n'
        tmp += '\t\t</blockTable>\n'
    return tmp


def votacao_vot_nom(lst_votacao_vot_nom):
    tmp = ''
    if lst_votacao_vot_nom:
        tmp += '\t\t<para style="P1">Votações Nominais - Matérias da Ordem do Dia</para>\n\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        tmp += '<blockTable style="repeater" repeatRows="1">\n'
        tmp += '<tr><td >Matéria</td><td>Votos</td></tr>\n'
        for votacao_vot_nom in lst_votacao_vot_nom:
            tmp += '<tr><td><para style="P3">' + str(votacao_vot_nom['titulo']) + '</para></td>'
            if votacao_vot_nom['votos']:
                tmp += '<td>'
                for v in votacao_vot_nom['votos']:
                    tmp += '<para style="P3"><b>' + str(v.parlamentar) + '</b> - ' + v.voto + '</para>'
                tmp += '</td>'
            else: 
                tmp += '<td><para style="P3"><b>Matéria não votada</b></para></td>'
            tmp += '</tr>\n'
        tmp += '\t\t</blockTable>\n'
    return tmp


def oradores_ordemdia(lst_oradores_ordemdia):
    tmp = ''
    if lst_oradores_ordemdia:
        tmp += '\t\t<para style="P1">Oradores da Ordem do Dia</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        for orador_ordemdia in lst_oradores_ordemdia:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>' + \
            str(orador_ordemdia['num_ordem']) + '</b> - ' + \
            orador_ordemdia['nome_parlamentar'] + '/' + \
            str(orador_ordemdia['sigla']) + ' - ' + \
            str(orador_ordemdia['observacao']) + '</para>\n'
    return tmp


def oradores(lst_oradores):
    tmp = ''
    if lst_oradores:
        tmp += '\t\t<para style="P1">Oradores das Explicações Pessoais</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> <br/></font>\n'
        tmp += '\t\t</para>\n'
        for orador in lst_oradores:
            tmp += '\t\t<para style="P2" spaceAfter="5"><b>' + \
                str(orador['num_ordem']) + '</b> - ' + orador['nom_parlamentar'] + \
                '/' + str(orador['sgl_partido']) + '</para>\n'
    return tmp


def ocorrencias(lst_ocorrencias):
    tmp = ''
    if lst_ocorrencias:
        tmp += '\t\t<para style="P1">Ocorrências da Sessão</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'
        for ocorrencia in lst_ocorrencias:
            tmp += '\t\t<para style="P3">' + \
                str(ocorrencia.conteudo) + '</para>\n'
            tmp += '\t\t<para style="P2">\n'
            tmp += '\t\t\t<font color="white"> </font>\n'
            tmp += '\t\t</para>\n'
    return tmp


def principal(rodape_dic, imagem, inf_basicas_dic, cont_mult_dic, lst_mesa, lst_presenca_sessao, lst_ausencia_sessao, lst_expedientes, lst_expediente_materia, lst_expediente_materia_vot_nom, lst_oradores_expediente, lst_presenca_ordem_dia, lst_votacao, lst_votacao_vot_nom, lst_oradores_ordemdia, lst_oradores, lst_ocorrencias):
    """
    """
    arquivoPdf = str(int(time.time() * 100)) + ".pdf"
    logger = logging.getLogger(__name__)

    tmp = ''
    tmp += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp += '<document filename="relatorio.pdf">\n'
    tmp += '\t<template pageSize="(21cm, 29.7cm)" title="Sessao Plenaria" author="Interlegis" allowSplitting="20">\n'
    tmp += '\t\t<pageTemplate id="first">\n'
    tmp += '\t\t\t<pageGraphics>\n'
    tmp += cabecalho(inf_basicas_dic, imagem)
    tmp += rodape(rodape_dic)
    tmp += '\t\t\t</pageGraphics>\n'
    tmp += '\t\t\t<frame id="first" x1="2cm" y1="4cm" width="17cm" height="20.5cm"/>\n'
    tmp += '\t\t</pageTemplate>\n'
    tmp += '\t</template>\n'
    tmp += paraStyle()
    tmp += '\t<story>\n'

    ordenacao = ResumoOrdenacao.objects.first()
    dict_ord_template = {
        'cont_mult': multimidia(cont_mult_dic),
        'exp': expedientes(lst_expedientes),
        'id_basica': inf_basicas(inf_basicas_dic),
        'lista_p': presenca(lst_presenca_sessao, lst_ausencia_sessao),
        'lista_p_o_d': presenca_ordem_dia(lst_presenca_ordem_dia),
        'mat_exp': expediente_materia(lst_expediente_materia),
        'v_n_mat_exp': expediente_materia_vot_nom(lst_expediente_materia_vot_nom),
        'mat_o_d': votacao(lst_votacao),
        'v_n_mat_o_d': votacao_vot_nom(lst_votacao_vot_nom),
        'mesa_d': mesa(lst_mesa),
        'oradores_exped': oradores_expediente(lst_oradores_expediente),
        'oradores_o_d': oradores_ordemdia(lst_oradores_ordemdia),
        'oradores_expli': oradores(lst_oradores),
        'ocorr_sessao': ocorrencias(lst_ocorrencias)
    }
    
    if ordenacao:
        try:
            tmp += dict_ord_template[ordenacao.primeiro]
            tmp += dict_ord_template[ordenacao.segundo]
            tmp += dict_ord_template[ordenacao.terceiro]
            tmp += dict_ord_template[ordenacao.quarto]
            tmp += dict_ord_template[ordenacao.quinto]
            tmp += dict_ord_template[ordenacao.sexto]
            tmp += dict_ord_template[ordenacao.setimo]
            tmp += dict_ord_template[ordenacao.oitavo]
            tmp += dict_ord_template[ordenacao.nono]
            tmp += dict_ord_template[ordenacao.decimo]
            tmp += dict_ord_template[ordenacao.decimo_primeiro]
            tmp += dict_ord_template[ordenacao.decimo_segundo]
            tmp += dict_ord_template[ordenacao.decimo_terceiro]
            tmp += dict_ord_template[ordenacao.decimo_quarto]
        except KeyError as e:
            logger.error("KeyError: " + str(e) + ". Erro ao tentar utilizar "
                              "configuração de ordenação. Utilizando ordenação padrão.")
            tmp += inf_basicas(inf_basicas_dic)
            tmp += multimidia(cont_mult_dic)
            tmp += mesa(lst_mesa)
            tmp += presenca(lst_presenca_sessao, lst_ausencia_sessao)
            tmp += expedientes(lst_expedientes)
            tmp += expediente_materia(lst_expediente_materia)
            tmp += expediente_materia_vot_nom(lst_expediente_materia_vot_nom)
            tmp += oradores_expediente(lst_oradores_expediente)
            tmp += presenca_ordem_dia(lst_presenca_ordem_dia)
            tmp += votacao(lst_votacao)
            tmp += votacao_vot_nom(lst_votacao_vot_nom)
            tmp += oradores_ordemdia(lst_oradores_ordemdia)
            tmp += oradores(lst_oradores)
            tmp += ocorrencias(lst_ocorrencias)

    else:
        tmp += inf_basicas(inf_basicas_dic)
        tmp += multimidia(cont_mult_dic)
        tmp += mesa(lst_mesa)
        tmp += presenca(lst_presenca_sessao, lst_ausencia_sessao)
        tmp += expedientes(lst_expedientes)
        tmp += expediente_materia(lst_expediente_materia)
        tmp += expediente_materia_vot_nom(lst_expediente_materia_vot_nom)
        tmp += oradores_expediente(lst_oradores_expediente)
        tmp += presenca_ordem_dia(lst_presenca_ordem_dia)
        tmp += votacao(lst_votacao)
        tmp += votacao_vot_nom(lst_votacao_vot_nom)
        tmp += oradores_ordemdia(lst_oradores_ordemdia)
        tmp += oradores(lst_oradores)
        tmp += ocorrencias(lst_ocorrencias)

    tmp += '\t</story>\n'
    tmp += '</document>\n'

    tmp_pdf = parseString(tmp)
    return tmp_pdf
#     if hasattr(context.temp_folder,arquivoPdf):
#         context.temp_folder.manage_delObjects(ids=arquivoPdf)
#     context.temp_folder.manage_addFile(arquivoPdf)
#     arq=context.temp_folder[arquivoPdf]
#     arq.manage_edit(title='Arquivo PDF temporario.',filedata=tmp_pdf,content_type='application/pdf')

#     return "/temp_folder/"+arquivoPdf

# return principal(cabecalho, rodape, sessao, imagem, inf_basicas_dic)
