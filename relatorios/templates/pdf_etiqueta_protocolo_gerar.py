# parameters=sessao,imagem,data,lst_protocolos,dic_cabecalho,lst_rodape,dic_filtro

"""relatorio_protocolo.py
   External method para gerar o arquivo rml da etiqueta de protocolo
   Autor: Luciano De Fazio
   Empresa: OpenLegis Consultoria
   versÃ£o: 1.0
"""
import time

from trml2pdf import parseString


def cabecalho(dic_cabecalho, imagem):
    """Gera o codigo rml do cabecalho"""
    tmp_data = ''
    tmp_data += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
        imagem + '"/>\n'
    tmp_data += '\t\t\t\t<lines>2cm 25.4cm 19cm 25.4cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica-Bold" size="15"/>\n'
    tmp_data += '\t\t\t\t<drawString x="5cm" y="27.2cm">' + \
        dic_cabecalho['nom_casa'] + '</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="12"/>\n'
    tmp_data += '\t\t\t\t<drawString x="5cm" y="26.6cm">Sistema de Apoio ao Processo Legislativo</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica-Bold" size="13"/>\n'
    tmp_data += '\t\t\t\t<drawString x="2.2cm" y="24.6cm">RelatÃ³rio de Controle do Protocolo</drawString>\n'

    return tmp_data


def rodape(lst_rodape):
    """Gera o codigo rml do rodape"""

    tmp_data = ''
    tmp_data += '\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp_data += '\t\t\t\t<drawString x="2cm" y="3.3cm">' + \
        lst_rodape[2] + '</drawString>\n'
    tmp_data += '\t\t\t\t<drawString x="17.9cm" y="3.3cm">PÃ¡gina <pageNumber/></drawString>\n'
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
    tmp_data += '\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="5.0" leading="6" alignment="CENTER"/>\n'
    tmp_data += '\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="8.0" leading="9" alignment="CENTER"/>\n'
    tmp_data += '\t</stylesheet>\n'

    return tmp_data


def protocolos(lst_protocolos, dic_cabecalho):
    """Gera o codigo rml do conteudo da pesquisa de protocolos"""

    tmp_data = ''

    # inicio do bloco que contem os flowables
    tmp_data += '\t<story>\n'

    for dic in lst_protocolos:
        # condicao para a quebra de pagina
        tmp_data += '\t\t<condPageBreak height="8mm"/>\n'

        # protocolos
        if dic['titulo'] != None:
            tmp_data += '\t\t<para style="P1">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'
            tmp_data += '\t\t<para style="P2"><b>' + \
                dic_cabecalho['nom_casa'] + '</b></para>\n'
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'
            tmp_data += '\t\t<barCode code="Code128" x="0.15cm" barHeight="0.34in" barWidth="0.018in">' + \
                dic['titulo'] + '</barCode>\n'
            tmp_data += '\t\t<para style="P2"><b>PROTOCOLO GERAL ' + \
                dic['titulo'] + '</b></para>\n'
        if dic['data'] != None:
            tmp_data += '\t\t<para style="P2"><b>' + \
                dic['data'] + '</b></para>\n'
        tmp_data += '\t\t<para style="P2"><b>' + \
            dic['natureza'] + '</b></para>\n'

    tmp_data += '\t</story>\n'
    return tmp_data


def principal(imagem, lst_protocolos, dic_cabecalho, lst_rodape):
    """Funcao pricipal que gera a estrutura global do arquivo rml"""

    arquivoPdf = str(int(time.time() * 100)) + ".pdf"

    tmp_data = ''
    tmp_data += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp_data += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp_data += '<document filename="etiquetas.pdf">\n'
    tmp_data += '\t<template pageSize="(62mm, 29mm)" title="Etiquetas de Protocolo" author="Luciano De Fazio" allowSplitting="20">\n'
    tmp_data += '\t\t<pageTemplate id="first">\n'
    tmp_data += '\t\t\t<pageGraphics>\n'
    tmp_data += '\t\t\t<frame id="first" x1="0.03cm" y1="0.1cm" width="61mm" height="29mm"/>\n'
    tmp_data += '\t\t\t</pageGraphics>\n'
    tmp_data += '\t\t</pageTemplate>\n'
    tmp_data += '\t</template>\n'
    tmp_data += paraStyle()
    tmp_data += protocolos(lst_protocolos, dic_cabecalho)
    tmp_data += '</document>\n'
    tmp_pdf = parseString(tmp_data)

    return tmp_pdf
#     if hasattr(context.temp_folder,arquivoPdf):
#         context.temp_folder.manage_delObjects(ids=arquivoPdf)
#     context.temp_folder.manage_addFile(arquivoPdf)
#     arq=context.temp_folder[arquivoPdf]
#     arq.manage_edit(title='Arquivo PDF temporÃ¡rio.',filedata=tmp_pdf,content_type='application/pdf')

#     return "/temp_folder/"+arquivoPdf

# return
# principal(sessao,imagem,data,lst_protocolos,dic_cabecalho,lst_rodape,dic_filtro)
