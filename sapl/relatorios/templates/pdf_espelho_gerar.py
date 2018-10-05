# parameters=sessao,imagem,data,lst_materias,dic_cabecalho,lst_rodape,dic_filtro

"""relatorio_materia.py
   External method para gerar o arquivo rml do resultado de uma pesquisa de matérias
   Autor: Leandro Gasparotto Valladares
   Empresa: Interlegis
   versão: 1.0
"""
import time

from trml2pdf import parseString


def cabecalho(dic_cabecalho, imagem):
    """Gera o codigo rml do cabecalho"""
    tmp_data = ''
    tmp_data += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
        imagem + '"/>\n'
    tmp_data += '\t\t\t\t<lines>2cm 25cm 19cm 25cm</lines>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="18"/>\n'
    tmp_data += '\t\t\t\t<drawString x="5cm" y="27.2cm">' + \
        dic_cabecalho['nom_casa'] + '</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="16"/>\n'
    tmp_data += '\t\t\t\t<drawString x="07cm" y="26.5cm">' + \
        dic_cabecalho['nom_estado'] + '</drawString>\n'
    tmp_data += '\t\t\t\t<setFont name="Helvetica" size="15"/>\n'
    tmp_data += '\t\t\t\t<drawCentredString x="10.5cm" y="25.2cm">SECRETARIA</drawCentredString>\n'
    return tmp_data


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
    tmp_data += '\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="13.0" leading="13" alignment="LEFT"/>\n'
    tmp_data += '\t</stylesheet>\n'
    return tmp_data


def materias(lst_materias):
    """Gera o codigo rml do conteudo da pesquisa de materias"""

    tmp_data = ''

    # inicio do bloco que contem os flowables
    tmp_data += '\t<story>\n'

    for dic in lst_materias:
        # espaco inicial
        #		tmp_data+='\t\t<para style="P2">\n'
        #		tmp_data+='\t\t\t<font color="white"> </font>\n'
        #		tmp_data+='\t\t</para>\n'
        #		tmp_data+='\t\t<para style="P2">\n'
        #		tmp_data+='\t\t\t<font color="white"> </font>\n'
        #		tmp_data+='\t\t</para>\n'

        # condicao para a quebra de pagina
        tmp_data += '\t\t<condPageBreak height="16cm"/>\n'

        # materias
#		if dic['titulo']!=None:
#			tmp_data+='\t\t<para style="P1">' + dic['titulo'] + '</para>\n'
#			tmp_data+='\t\t<para style="P1">\n'
#			tmp_data+='\t\t\t<font color="white"> </font>\n'
#			tmp_data+='\t\t</para>\n'

        if dic['materia'] != None:
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'
            tmp_data += '\t\t<para style="P2"><b>INDICAÇÃO:</b> ' + \
                dic['materia'] + '</para>\n'
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'

        if dic['dat_apresentacao'] != None:
            tmp_data += '\t\t<para style="P2"><b>DATA DE ENTRADA:</b> ' + \
                dic['dat_apresentacao'] + '</para>\n'
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'

        if dic['nom_autor'] != None:
            tmp_data += '\t\t<para style="P2"><b>AUTOR:</b> ' + \
                dic['nom_autor'] + '</para>\n'
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'

        if dic['txt_ementa'] != None:
            txt_ementa = dic['txt_ementa'].replace('&', '&amp;')
            tmp_data += '\t\t<para style="P2"><b>EMENTA:</b> ' + \
                dic['txt_ementa'] + '</para>\n'
            tmp_data += '\t\t<para style="P2">\n'
            tmp_data += '\t\t\t<font color="white"> </font>\n'
            tmp_data += '\t\t</para>\n'

    tmp_data += '\t</story>\n'
    return tmp_data


def principal(imagem, lst_materias, dic_cabecalho, lst_rodape):
    """Funcao pricipal que gera a estrutura global do arquivo rml"""

#	if sessao:
#		arquivoPdf=sessao+".pdf"
#	else:
#		arquivoPdf=str(int(time.time()*100))+".pdf"
    arquivoPdf = str(int(time.time() * 100)) + ".pdf"

    tmp_data = ''
    tmp_data += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp_data += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp_data += '<document filename="relatorio.pdf">\n'
    tmp_data += '\t<template pageSize="(21cm, 29.7cm)" title="Relatorio de Materias" author="Interlegis" allowSplitting="20">\n'
    tmp_data += '\t\t<pageTemplate id="first">\n'
    tmp_data += '\t\t\t<pageGraphics>\n'
    tmp_data += cabecalho(dic_cabecalho, imagem)
    tmp_data += rodape(lst_rodape)
    tmp_data += '\t\t\t</pageGraphics>\n'
    tmp_data += '\t\t\t<frame id="first" x1="2cm" y1="4cm" width="17cm" height="21cm"/>\n'
    tmp_data += '\t\t</pageTemplate>\n'
    tmp_data += '\t</template>\n'
    tmp_data += paraStyle()
    tmp_data += materias(lst_materias)
    tmp_data += '</document>\n'
    tmp_pdf = parseString(tmp_data)

    return tmp_pdf
# 	try:
#   	  tmp_pdf=parseString(unicode(tmp_data, 'utf-8'))
#   	except:
#   	  tmp_pdf=parseString(unicode(tmp_data, 'utf-8'))

#         if hasattr(context.temp_folder,arquivoPdf):
#             context.temp_folder.manage_delObjects(ids=arquivoPdf)
#         context.temp_folder.manage_addFile(arquivoPdf)
#         arq=context.temp_folder[arquivoPdf]
#         arq.manage_edit(title='Arquivo PDF temporário.',filedata=tmp_pdf,content_type='application/pdf')

#         return "/temp_folder/"+arquivoPdf

# return
# principal(sessao,imagem,data,lst_materias,dic_cabecalho,lst_rodape,dic_filtro)
