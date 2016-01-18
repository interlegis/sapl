##parameters=sessao,imagem,data,lst_protocolos,dic_cabecalho,lst_rodape,dic_filtro

"""relatorio_protocolo.py
   External method para gerar o arquivo rml da etiqueta de protocolo
   Autor: Luciano De Fazio
   Empresa: OpenLegis Consultoria
   versão: 1.0
"""
import time

from trml2pdf import parseString


def paraStyle():
    """Gera o codigo rml que define o estilo dos paragrafos"""

    tmp_data=''
    tmp_data+='\t<stylesheet>\n'
    tmp_data+='\t\t<blockTableStyle id="Standard_Outline">\n'
    tmp_data+='\t\t\t<blockAlignment value="LEFT"/>\n'
    tmp_data+='\t\t\t<blockValign value="TOP"/>\n'
    tmp_data+='\t\t</blockTableStyle>\n'
    tmp_data+='\t\t<initialize>\n'
    tmp_data+='\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp_data+='\t\t</initialize>\n'
    tmp_data+='\t\t<paraStyle name="P1" fontName="Helvetica" fontSize="9" leading="11" alignment="justify"/>\n'
    tmp_data+='\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="8" leading="9" alignment="right"/>\n'
    tmp_data+='\t\t<paraStyle name="P3" fontName="Helvetica" fontSize="9" leading="9" alignment="justify"/>\n'
    tmp_data+='\t</stylesheet>\n'

    return tmp_data

def protocolos(lst_protocolos):
    """Gera o codigo rml do conteudo da pesquisa de protocolos"""

    tmp_data=''

    #inicio do bloco que contem os flowables
    tmp_data+='\t<story>\n'

    for dic in lst_protocolos:
        #condicao para a quebra de pagina
        tmp_data+='\t\t<condPageBreak height="3cm"/>\n'

        #protocolos
        tmp_data+='\t\t<barCode code="Code128" x="5.6cm" barHeight="0.3in" barWidth="0.012in">' +dic['titulo']+ '</barCode>\n'
        tmp_data+='\t\t<para style="P2"><b>Protocolo:</b> ' +dic['titulo']+ '</para>\n'
        tmp_data+='\t\t<para style="P2">'+ dic['data']+ '</para>\n'
        tmp_data+='\t\t<para style="P1"><b>'+dic['numeracao']+'</b></para>\n'
        tmp_data+='\t\t<para style="P1"><b>'+dic['sgl_processo']+' '+dic['ident_processo']+ ' '+dic['num_processo']+ '</b></para>\n'
        tmp_data+='\t\t<para style="P1"><b>Autor:</b> <font size="8">' +dic['nom_autor']+ '</font></para>\n'
        tmp_data+='\t\t<para style="P2">\n'
        tmp_data+='\t\t\t<font color="white"> </font>\n'
        tmp_data+='\t\t</para>\n'
        tmp_data+='\t\t<para style="P3"><b>Ementa:</b> <font size="8">' +dic['txt_assunto']+ '</font></para>\n'

    tmp_data+='\t</story>\n'
    return tmp_data

def principal(sessao,imagem,data,lst_protocolos,dic_cabecalho,lst_rodape,dic_filtro={}):
    """Funcao pricipal que gera a estrutura global do arquivo rml"""

    arquivoPdf=str(int(time.time()*100))+".pdf"

    tmp_data=''
    tmp_data+='<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp_data+='<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp_data+='<document filename="etiquetas.pdf">\n'
    tmp_data+='\t<template pageSize="(10cm, 6.2cm)" title="Etiquetas de Protocolo" author="Luciano De Fazio" allowSplitting="20" rightMargin="3mm" showBoundary="0">\n'
    tmp_data+='\t\t<pageTemplate id="main">\n'
    tmp_data+='\t\t<pageGraphics>\n'
    tmp_data+='\t\t</pageGraphics>\n'
    tmp_data+='\t\t\t<frame id="first" x1="4mm" y1="1mm" width="94mm" height="60mm"/>\n'
    tmp_data+='\t\t</pageTemplate>\n'
    tmp_data+='\t</template>\n'
    tmp_data+=paraStyle()
    tmp_data+=protocolos(lst_protocolos)
    tmp_data+='</document>\n'
    tmp_pdf=parseString(tmp_data)

    return tmp_pdf

#     if hasattr(context.temp_folder,arquivoPdf):
#         context.temp_folder.manage_delObjects(ids=arquivoPdf)
#     context.temp_folder.manage_addFile(arquivoPdf)
#     arq=context.temp_folder[arquivoPdf]
#     arq.manage_edit(title='Arquivo PDF temporário.',filedata=tmp_pdf,content_type='application/pdf')

#     return "/temp_folder/"+arquivoPdf

# return principal(sessao,imagem,data,lst_protocolos,dic_cabecalho,lst_rodape,dic_filtro)
