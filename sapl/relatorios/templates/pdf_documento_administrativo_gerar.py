# parameters=sessao,imagem,data,lst_documentos,dic_cabecalho,lst_rodape,dic_filtro

"""relatorio_documento.py
   External method para gerar o arquivo rml do resultado
    de uma pesquisa de documentos administrativos
   Autor: Luciano De Fazio
   Empresa: OpenLegis Consultoria
   versão: 1.0
"""
import time
import os

from trml2pdf import parseString


def cabecalho(dic_cabecalho, imagem):
    """Gera o codigo rml do cabecalho"""
    tmp_data = ''
    if os.path.isfile(imagem):
        tmp_data += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
            imagem + '"/>\n'
    tmp_data += '\t\t\t\t<lines>2cm 25.4cm 19cm 25.4cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica-Bold" size="15"/>\n'
    tmp_data += '\t\t\t\t<drawString x="5cm" y="27.2cm">' + \
        dic_cabecalho['nom_casa'] + '</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="12"/>\n'
    tmp_data += '\t\t\t\t<drawString x="5cm" y="26.6cm">Sistema de Apoio ao Processo Legislativo</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica-Bold" size="13"/>\n'
    tmp_data += '\t\t\t\t<drawString x="2.2cm" y="24.6cm">Relatório de Documentos Administrativos</drawString>\n'

    return tmp_data


def rodape(lst_rodape):
    """Gera o codigo rml do rodape"""

    tmp_data = ''
    tmp_data += '\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp_data += '\t\t\t\t<drawString x="2cm" y="3.3cm">' + \
        lst_rodape[2] + '</drawString>\n'
    tmp_data += '\t\t\t\t<drawString x="17.9cm" y="3.3cm">Página <pageNumber/></drawString>\n'
    tmp_data += '\t\t\t\t<drawCentredString x="10.5cm" y="2.7cm">' + \
        lst_rodape[0] + '</drawCentredString>\n'
    tmp_data += '\t\t\t\t<drawCentredString x="10.5cm" y="2.3cm">' + \
        lst_rodape[1] + '</drawCentredString>\n'

    return tmp_data


def paraStyle():
    """Gera o codigo rml que define o estilo dos paragrafos"""

    tmp_data = ''
    tmp_data += '\t<stylesheet>\n'
    tmp_data += '\t\t<blockTableStyle id="Standard_Outline">\n'
    tmp_data += '\t\t\t<blockAlignment value="LEFT"/>\n'
    tmp_data += '\t\t\t<blockValign value="TOP"/>\n'
    tmp_data += '\t\t</blockTableStyle>\n'
    tmp_data += '\t\t<initialize>\n'
    tmp_data += '\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp_data += '\t\t</initialize>\n'
    tmp_data += '\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="10.0" leading="10" alignment="CENTER"/>\n'
    tmp_data += '\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="10.0" leading="12" alignment="justify"/>\n'
    tmp_data += '\t</stylesheet>\n'

    return tmp_data


def documentos(lst_documentos):
    """Gera o codigo rml do conteudo da pesquisa de documentos administrativos"""

    tmp_data = ''

    # inicio do bloco que contem os flowables
    tmp_data += '\t<story>\n'

    for dic in lst_documentos:
        # espaco inicial
        tmp_data += '\t\t<para style="P2">\n'
        tmp_data += '\t\t\t<font color="white"> </font>\n'
        tmp_data += '\t\t</para>\n'
        tmp_data += '\t\t<para style="P2">\n'
        tmp_data += '\t\t\t<font color="white"> </font>\n'
        tmp_data += '\t\t</para>\n'

        # condicao para a quebra de pagina
        tmp_data += '\t\t<condPageBreak height="2cm"/>\n'

        # materias
        if dic['titulo'] != None:
            tmp_data += '\t\t<para style="P1">' + dic['titulo'] + '</para>\n'
            tmp_data += '\t\t<para style="P1">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'
        if dic['txt_assunto'] != None:
            txt_assunto = dic['txt_assunto'].replace('&', '&amp;')
            tmp_data += '\t\t<para style="P2">' + txt_assunto + '</para>\n'

        if dic['txt_interessado'] != None:
            tmp_data += '\t\t<para style="P2"><b>Interessado:</b> ' + \
                dic['txt_interessado'] + '</para>\n'
        if dic['localizacao_atual'] != None:
            tmp_data += '\t\t<para style="P2"><b>Localização Atual:</b> ' + \
                dic['localizacao_atual'] + '</para>\n'
        if dic['des_situacao'] != None:
            tmp_data += '\t\t<para style="P2"><b>Situação:</b> ' + \
                dic['des_situacao'] + '</para>\n'
        if dic['ultima_acao'] != None:
            tmp_data += '\t\t<para style="P2"><b>Última Ação:</b> ' + \
                dic['ultima_acao'] + '</para>\n'

    tmp_data += '\t</story>\n'
    return tmp_data


def principal(imagem, lst_documentos, dic_cabecalho, lst_rodape):
    """Funcao pricipal que gera a estrutura global do arquivo rml"""

    arquivoPdf = str(int(time.time() * 100)) + ".pdf"

    tmp_data = ''
    tmp_data += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp_data += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp_data += '<document filename="relatorio.pdf">\n'
    tmp_data += '\t<template pageSize="(21cm, 29.7cm)" title="Relatorio de Documentos Administrativos" author="OpenLegis" allowSplitting="20">\n'
    tmp_data += '\t\t<pageTemplate id="first">\n'
    tmp_data += '\t\t\t<pageGraphics>\n'
    tmp_data += cabecalho(dic_cabecalho, imagem)
    tmp_data += rodape(lst_rodape)
    tmp_data += '\t\t\t</pageGraphics>\n'
    tmp_data += '\t\t\t<frame id="first" x1="2cm" y1="3.5cm" width="17cm" height="21cm"/>\n'
    tmp_data += '\t\t</pageTemplate>\n'
    tmp_data += '\t</template>\n'
    tmp_data += paraStyle()
    tmp_data += documentos(lst_documentos)
    tmp_data += '</document>\n'
    tmp_pdf = parseString(tmp_data)

    return tmp_pdf

#     if hasattr(context.temp_folder,arquivoPdf):
#         context.temp_folder.manage_delObjects(ids=arquivoPdf)
#     context.temp_folder.manage_addFile(arquivoPdf)
#     arq=context.temp_folder[arquivoPdf]
#     arq.manage_edit(title='Arquivo PDF temporário.',filedata=tmp_pdf,content_type='application/pdf')

#     return "/temp_folder/"+arquivoPdf

# return
# principal(sessao,imagem,data,lst_documentos,dic_cabecalho,lst_rodape,dic_filtro)
