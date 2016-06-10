# parameters=sessao,imagem,dat_ordem,lst_splen,lst_pauta,dic_cabecalho,lst_rodape

"""relatorio_ordem.py
   External method para gerar o arquivo rml da ordem do dia
   Autor: Leandro Gasparotto Valladares
   Empresa: Interlegis
   versão: 1.0
"""
import os
import time

from trml2pdf import parseString


def cabecalho(dic_cabecalho, dat_ordem, imagem):
    """Gera o codigo rml do cabecalho"""

    tmp = ''
    tmp += '\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + \
        imagem + '"/>\n'
    tmp += '\t\t\t\t<lines>2cm 25cm 19cm 25cm</lines>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="12"/>\n'
    #tmp+='\t\t\t\t<drawString x="4cm" y="27.2cm">' + str(dic_cabecalho['nom_casa']) + '</drawString>\n'
    #tmp+='\t\t\t\t<setFont name="Helvetica" size="14"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="27.2cm">' + \
        str(dic_cabecalho['nom_estado']) + '</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="14"/>\n'
    tmp += '\t\t\t\t<drawString x="5cm" y="26.5cm">' + \
        str(dic_cabecalho['nom_casa']) + '</drawString>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="14"/>\n'
    #tmp+='\t\t\t\t<drawString x="5cm" y="27.9cm">' + "Palacio 11 de Outubro" + '</drawString>\n'
    #tmp+='\t\t\t\t<setFont name="Helvetica" size="10"/>\n'

    tmp += '\t\t\t\t<drawCentredString x="10.5cm" y="25.2cm">Relatório da Ordem do Dia</drawCentredString>\n'

    return tmp


def rodape(lst_rodape):
    """ Gera o codigo rml do rodape"""

    tmp = ''
    tmp += '\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp += '\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp += '\t\t\t\t<drawString x="2cm" y="3.3cm">' + \
        lst_rodape[2] + '</drawString>\n'
    tmp += '\t\t\t\t<drawString x="17.9cm" y="3.3cm">Página <pageNumber/></drawString>\n'
    tmp += '\t\t\t\t<drawCentredString x="10.5cm" y="2.7cm">' + \
        lst_rodape[0] + '</drawCentredString>\n'
    tmp += '\t\t\t\t<drawCentredString x="10.5cm" y="2.3cm">' + \
        lst_rodape[1] + '</drawCentredString>\n'

    return tmp


def paraStyle():
    """ Gera o codigo rml que define o estilo dos paragrafos"""

    tmp = ''
    tmp += '\t<stylesheet>\n'
    tmp += '\t\t<blockTableStyle id="Standard_Outline">\n'
    tmp += '\t\t\t<blockAlignment value="LEFT"/>\n'
    tmp += '\t\t\t<blockValign value="TOP"/>\n'
    tmp += '\t\t</blockTableStyle>\n'
    tmp += '\t\t<initialize>\n'
    tmp += '\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp += '\t\t</initialize>\n'
    tmp += '\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="12.0" leading="12" alignment="CENTER"/>\n'
    tmp += '\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="9.0" leading="10" alignment="LEFT"/>\n'
    tmp += '\t\t<paraStyle name="P3" fontName="Helvetica" fontSize="10.0" leading="10" alignment="JUSTIFY"/>\n'
    tmp += '\t</stylesheet>\n'

    return tmp

# def splen(lst_splen):


def pauta(lst_splen, lst_pauta):
    """ Funcao que gera o codigo rml da sessao plenaria """

    tmp = ''

    # inicio do bloco
    tmp += '\t<story>\n'

    for dicsp in lst_splen:
        # espaço inicial
        tmp += '\t\t<para style="P1">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'
        tmp += '\t\t<para style="P1">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'

        # condicao para a quebra de pagina
        tmp += '\t\t<condPageBreak height="4cm"/>\n'

        # sessao plenaria
        if dicsp['sessao'] != None:
            tmp += '\t\t<para style="P1">' + \
                dicsp['sessao'].replace('&', '&amp;') + '</para>\n'
            tmp += '\t\t<para style="P1">\n'
            tmp += '\t\t\t<font color="white"> </font>\n'
            tmp += '\t\t</para>\n'

        if dicsp['datasessao'] != None:
            tmp += '\t\t<para style="P1">' + \
                dicsp['datasessao'].replace('&', '&amp;') + '</para>\n'
            tmp += '\t\t<para style="P1">\n'
            tmp += '\t\t\t<font color="white"> </font>\n'
            tmp += '\t\t</para>\n'

#    tmp+='\t</story>\n'
#    return tmp
#
# def pauta(lst_pauta):
#    """ Funcao que gera o codigo rml da pauta da ordem do dia"""

#    tmp=''

    # inicio do bloco que contem os flowables
#    tmp+='\t<story>\n'

    for dic in lst_pauta:
        # espaco inicial
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'
        tmp += '\t\t<para style="P2">\n'
        tmp += '\t\t\t<font color="white"> </font>\n'
        tmp += '\t\t</para>\n'

        # condicao para a quebra de pagina
        tmp += '\t\t<condPageBreak height="4cm"/>\n'

        # pauta
        if dic['num_ordem'] != None:
            tmp += '\t\t<para style="P2">Item nº ' + \
                str(dic['num_ordem']) + '</para>'
        if dic['id_materia'] != None:
            tmp += '\t\t<para style="P1">' + dic['id_materia'] + '</para>\n'
            tmp += '\t\t<para style="P1">\n'
            tmp += '\t\t\t<font color="white"> </font>\n'
            tmp += '\t\t</para>\n'
        if dic['txt_ementa'] != None:
            tmp += '\t\t<para style="P3">' + \
                dic['txt_ementa'].replace('&', '&amp;') + '</para>\n'
            tmp += '\t\t<para style="P3">\n'
            tmp += '\t\t\t<font color="white"> </font>\n'
            tmp += '\t\t</para>\n'
        if dic['des_numeracao'] != None:
            tmp += '\t\t<para style="P2"><b>Processo:</b> ' + \
                dic['des_numeracao'] + '</para>\n'
        if dic['des_turno'] != None:
            tmp += '\t\t<para style="P2"><b>Turno:</b> ' + \
                dic['des_turno'] + '</para>\n'
        if dic['nom_autor'] != None:
            tmp += '\t\t<para style="P2"><b>Autor:</b> ' + \
                dic['nom_autor'] + '</para>\n'
        if dic['des_situacao'] != None:
            tmp += '\t\t<para style="P2"><b>Situação:</b> ' + \
                dic['des_situacao'] + '</para>\n'
#       if dic['des_numeracao']!=None:
#           tmp+='\t\t<para style="P2"><b>Processo Nº:</b> ' + dic['des_numeracao'] + '</para>\n'


#        indice = 0
#        for relator in dic['lst_relator']:
#            indice = indice + 1
#            if (relator != None):
#                if (indice < 2):
#                    tmp+='\t\t<xpre style="P2"><b>Relator</b>: ' + relator + '</xpre>\n'
#                else:
#                    tmp+='\t\t<pre style="P2">              ' + relator + '</pre>\n'

    tmp += '\t</story>\n'
    return tmp


def principal(imagem, lst_splen, lst_pauta, dic_cabecalho, lst_rodape):
    """Funcao principal que gera a estrutura global do arquivo rml contendo o relatorio de uma ordem do dia.
    ordem_dia_[data da ordem do dia do relatório].pdf
    Retorna:
    Parâmetros:
    dat_ordem       => A data da ordem do dia.
        splen       => Uma lista de dicionários contendo as sessões plenárias do dia.
        pauta       => Uma lista de dicionários contendo a pauta da ordem do dia numa sessão plenária.
        cabecalho   => Um dicionário contendo informações para o Cabeçalho do relatório, incluindo a imagem.
        rodapé      => Uma lista contendo informações para o Rodapé do relatório.
    """

    arquivoPdf = str(int(time.time() * 100)) + ".pdf"

    tmp = ''
    tmp += '<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp += '<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp += '<document filename="relatorio.pdf">\n'
    tmp += '\t<template pageSize="(21cm, 29.7cm)" title="Relatorio de Materias" author="Interlegis" allowSplitting="20">\n'
    tmp += '\t\t<pageTemplate id="first">\n'
    tmp += '\t\t\t<pageGraphics>\n'
    tmp += cabecalho(dic_cabecalho, dat_ordem, imagem)
    tmp += rodape(lst_rodape)
    tmp += '\t\t\t</pageGraphics>\n'
    tmp += '\t\t\t<frame id="first" x1="2cm" y1="4cm" width="17cm" height="21cm"/>\n'
    tmp += '\t\t</pageTemplate>\n'
    tmp += '\t</template>\n'
    tmp += paraStyle()
#   tmp+=splen(lst_splen)
    tmp += pauta(lst_splen, lst_pauta)
    tmp += '</document>\n'
    tmp_pdf = parseString(tmp)

    return tmp_pdf

# try:
# tmp_pdf=parseString(unicode(tmp, 'utf-8'))
# except:
# tmp_pdf=parseString(unicode(tmp, 'utf-8'))

#     if hasattr(context.temp_folder, arquivoPdf):
#         context.temp_folder.manage_delObjects(ids=arquivoPdf)
#     context.temp_folder.manage_addFile(arquivoPdf)
#     arq = context.temp_folder[arquivoPdf]
#     arq.manage_edit(title='Arquivo PDF temporário.',
#                     filedata=tmp_pdf, content_type='application/pdf')

#     return "/temp_folder/" + arquivoPdf

# return principal(sessao, imagem, dat_ordem, lst_splen, lst_pauta,
# dic_cabecalho, lst_rodape)
