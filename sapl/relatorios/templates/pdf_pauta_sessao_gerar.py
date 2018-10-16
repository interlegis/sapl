##parameters=rodape_dic, sessao='', imagem, inf_basicas_dic, lst_votacao, lst_expediente_materia
"""Script para geração do PDF das pautas das sessoes plenarias
   Autor Luciano De Fázio - 06/11/2012
   versão: 1.0
"""
import time

from trml2pdf import parseString


def cabecalho(inf_basicas_dic, imagem):
    """
    """
    tmp = ''
    tmp += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
        imagem + '"/>\n'
    tmp += '\t\t\t\t<lines>2cm 25.4cm 19cm 25.4cm</lines>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica-Bold" size="14"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="27.2cm">' + \
        str(inf_basicas_dic["nom_camara"]) + '</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="12"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="26.6cm">Sistema de Apoio ao Processo Legislativo</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica-Bold" size="12"/>\n'
    tmp += '\t\t\t\t<drawString x="4.2cm" y="25cm">Pauta da ' + str(inf_basicas_dic['num_sessao_plen']) + 'ª Reunião ' + str(inf_basicas_dic['nom_sessao']) + ' da ' + str(
        inf_basicas_dic['num_sessao_leg']) + 'ª Sessão Legislativa da </drawString>\n'
    tmp += '\t\t\t\t<drawString x="6.7cm" y="24.5cm">' + \
        str(inf_basicas_dic['num_legislatura']) + \
        ' Legislatura </drawString>\n'
    return tmp


def rodape(lst_rodape):
    """Gera o codigo rml do rodape"""
    tmp_data = ''
    tmp_data += '\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp_data += '\t\t\t\t<drawString x="2cm" y="3.3cm">' + \
        lst_rodape[2] + '</drawString>\n'
    tmp_data += '\t\t\t\t<drawCentredString x="10.5cm" y="2.7cm">' + \
        lst_rodape[0] + '</drawCentredString>\n'
    tmp_data += '\t\t\t\t<drawCentredString x="10.5cm" y="2.3cm">' + \
        lst_rodape[1] + '</drawCentredString>\n'
    return tmp_data


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
    tmp += '\t\t\t<blockAlignment value="LEFT"/>\n'
    tmp += '\t\t\t<blockValign value="TOP"/>\n'
    tmp += '\t\t</blockTableStyle>\n'
    tmp += '\t\t<initialize>\n'
    tmp += '\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp += '\t\t</initialize>\n'
    tmp += '\t\t<paraStyle name="style.Title" fontName="Helvetica" fontSize="11" leading="13" alignment="RIGHT"/>\n'
    tmp += '\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="12.0" textColor="silver" leading="14" spaceBefore="12" alignment="LEFT"/>\n'
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
    num_sessao_plen = inf_basicas_dic["num_sessao_plen"]
    num_sessao_leg = inf_basicas_dic["num_sessao_leg"]
    num_legislatura = inf_basicas_dic["num_legislatura"]
    dat_inicio_sessao = inf_basicas_dic["dat_inicio_sessao"]
    hr_inicio_sessao = inf_basicas_dic["hr_inicio_sessao"]
    dat_fim_sessao = inf_basicas_dic["dat_fim_sessao"]
    hr_fim_sessao = inf_basicas_dic["hr_fim_sessao"]

    tmp += '\t\t<para style="P1">Informações Básicas</para>\n'
    tmp += '\t\t<para style="P2">\n'
    tmp += '\t\t\t<font color="white"> </font>\n'
    tmp += '\t\t</para>\n'
    tmp += '\t\t<para style="P2" spaceAfter="5"><b>Tipo da Sessão: </b> ' + \
        nom_sessao + '</para>\n'
    tmp += '\t\t<para style="P2" spaceAfter="5"><b>Abertura: </b> ' + \
        dat_inicio_sessao.strftime(
            "%d/%m/%Y") + ' <b>- </b> ' + hr_inicio_sessao + '</para>\n'

    return tmp


def expediente_materia(lst_expediente_materia):
    """
    """
    tmp = ''
    tmp += '<para style="P1">Matérias do Expediente</para>\n\n'
    tmp += '\t\t<para style="P2">\n'
    tmp += '\t\t\t<font color="white"> </font>\n'
    tmp += '\t\t</para>\n'
    tmp += '<blockTable style="repeater" repeatRows="1">\n'
    tmp += '<tr><td >Matéria</td><td>Ementa</td><td>Situação</td></tr>\n'
    for expediente_materia in lst_expediente_materia:
        tmp += '<tr><td><para style="P3"><b>' + str(expediente_materia['num_ordem']) + '</b> - ' + \
               expediente_materia["tipo_materia"] + ' No. ' + \
               expediente_materia['id_materia'] + '</para>\n' + '<para style="P3"><b>Autor: </b>' + \
               expediente_materia['nom_autor'] + '</para></td>\n'
        txt_ementa = expediente_materia['txt_ementa'].replace('&', '&amp;')
        tmp += '<td><para style="P4">' + txt_ementa + '</para></td>\n'
        tmp += '<td><para style="P3">' + \
            str(expediente_materia['des_situacao']) + '</para></td></tr>\n'

    tmp += '\t\t</blockTable>\n'
    return tmp


def votacao(lst_votacao):
    """
    """

    tmp = ''
    tmp += '<para style="P1">Matérias da Ordem do Dia</para>\n\n'
    tmp += '\t\t<para style="P2">\n'
    tmp += '\t\t\t<font color="white"> </font>\n'
    tmp += '\t\t</para>\n'
    tmp += '<blockTable style="repeater" repeatRows="1">\n'
    tmp += '<tr><td >Matéria</td><td >Ementa</td><td>Situação</td></tr>\n'
    for votacao in lst_votacao:
        tmp += '<tr><td><para style="P3"><b>' + str(votacao['num_ordem']) + '</b> - ' + \
               votacao["tipo_materia"] + ' No. ' + \
               str(votacao['id_materia']) + '</para>\n' + '<para style="P3"><b>Processo: </b>' + \
               str(votacao['des_numeracao']) + '</para>\n' + '<para style="P3"><b>Turno: </b>' + \
               str(votacao['des_turno']) + '</para>\n' + '<para style="P3"><b>Autor: </b>' + \
               str(votacao['nom_autor']) + '</para></td>\n'
        tmp += '<td><para style="P4">' + \
            str(votacao['txt_ementa']) + '</para></td>\n'
        tmp += '<td><para style="P3">' + \
            str(votacao['des_situacao']) + '</para></td></tr>\n'

    tmp += '\t\t</blockTable>\n'
    return tmp


def principal(cabecalho_dic, rodape_dic, sessao, imagem, inf_basicas_dic, lst_expediente_materia, lst_votacao):
    """
    """

    arquivoPdf = str(int(time.time() * 100)) + ".pdf"

    tmp = ''
    tmp += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp += '<document filename="relatorio.pdf">\n'
    tmp += '\t<template pageSize="(21cm, 29.7cm)" title="Pauta da Sessao Plenaria" author="Interlegis" allowSplitting="20">\n'
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
    tmp += inf_basicas(inf_basicas_dic)
    tmp += expediente_materia(lst_expediente_materia)
    tmp += votacao(lst_votacao)
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
