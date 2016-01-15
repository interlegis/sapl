##parameters=imagem, dic_rodape,dic_inf_basicas,dic_orig_externa,lst_mat_anexadas,lst_autoria,lst_des_iniciais,dic_tramitacoes,lst_relatorias,lst_numeracoes,lst_leg_citadas,lst_acessorios,sessao=''

"""relatorio_detalhe_materia.py
   External method para gerar o arquivo rml do resultado da pesquisa de uma matéria
   Autor: Leandro Gasparotto Valladares
   Empresa: Interlegis
   versão: 1.0
"""
import time
from cStringIO import StringIO

from trml2pdf import parseString


def cabecalho(dic_inf_basicas,imagem):
    """
    Função que gera o código rml do cabeçalho da página
    """

    tmp=''
    tmp+='\t\t\t\t<image x="2.1cm" y="25.7cm" width="59" height="62" file="' + imagem + '"/>\n'
    tmp+='\t\t\t\t<lines>2cm 24.5cm 19cm 24.5cm</lines>\n'
    if dic_inf_basicas['nom_camara']!="" and dic_inf_basicas['nom_camara']!=None:
        tmp+='\t\t\t\t<setFont name="Helvetica" size="16"/>\n'
        tmp+='\t\t\t\t<drawString x="5cm" y="27.2cm">' + dic_inf_basicas['nom_camara'] + '</drawString>\n'
    tmp+='\t\t\t\t<setFont name="Helvetica" size="14"/>\n'
    tmp+='\t\t\t\t<drawString x="5cm" y="26.5cm">Sistema de Apoio ao Processo Legislativo</drawString>\n'
    if str(dic_inf_basicas['nom_projeto']) != "" and str(dic_inf_basicas['nom_projeto']) != None:
        tmp+='\t\t\t\t<setFont name="Helvetica" size="15"/>\n'
        tmp+='\t\t\t\t<drawCentredString x="10.5cm" y="25.2cm">' + str(dic_inf_basicas['nom_projeto']) + '</drawCentredString>\n'
    if str(dic_inf_basicas['cod_projeto']) != "" and str(dic_inf_basicas['cod_projeto']) != None:
        tmp+='\t\t\t\t<setFont name="Helvetica" size="15"/>\n'
        tmp+='\t\t\t\t<drawCentredString x="10.5cm" y="24.7cm">' + str(dic_inf_basicas['cod_projeto']) + '</drawCentredString>\n'
    return tmp

def rodape(dic_rodape):
    """
    Função que gera o codigo rml do rodape da pagina.
    """

    tmp=''
    linha1 = dic_rodape['end_casa']
    if dic_rodape['end_casa']!="" and dic_rodape['end_casa']!=None:
        linha1 = linha1 + " - "
    if dic_rodape['num_cep']!="" and dic_rodape['num_cep']!=None:
        linha1 = linha1 + "CEP " + dic_rodape['num_cep']
    if dic_rodape['nom_localidade']!="" and dic_rodape['nom_localidade']!=None:
        linha1 = linha1 + " - " + dic_rodape['nom_localidade']
    if dic_rodape['sgl_uf']!="" and dic_rodape['sgl_uf']!=None:
        inha1 = linha1 + " " + dic_rodape['sgl_uf']
    if dic_rodape['num_tel']!="" and dic_rodape['num_tel']!=None:
        linha1 = linha1 + " Tel: "+ dic_rodape['num_tel']
    if dic_rodape['end_web_casa']!="" and dic_rodape['end_web_casa']!=None:
        linha2 = dic_rodape['end_web_casa']
    if dic_rodape['end_email_casa']!="" and dic_rodape['end_email_casa']!=None:
        linha2 = linha2 + " - E-mail: " + dic_rodape['end_email_casa']
    if dic_rodape['data_emissao']!="" and dic_rodape['data_emissao']!=None:
        data_emissao = dic_rodape['data_emissao']

    tmp+='\t\t\t\t<lines>2cm 3.2cm 19cm 3.2cm</lines>\n'
    tmp+='\t\t\t\t<setFont name="Helvetica" size="8"/>\n'
    tmp+='\t\t\t\t<drawString x="2cm" y="3.3cm">' + data_emissao + '</drawString>\n'
    tmp+='\t\t\t\t<drawString x="17.9cm" y="3.3cm">Página <pageNumber/></drawString>\n'
    tmp+='\t\t\t\t<drawCentredString x="10.5cm" y="2.7cm">' + linha1 + '</drawCentredString>\n'
    tmp+='\t\t\t\t<drawCentredString x="10.5cm" y="2.3cm">' + linha2 + '</drawCentredString>\n'

    return tmp

def paraStyle():
    """Função que gera o código rml que define o estilo dos parágrafos"""
    
    tmp=''
    tmp+='\t<stylesheet>\n'
    tmp+='\t\t<blockTableStyle id="Standard_Outline">\n'
    tmp+='\t\t\t<blockAlignment value="LEFT"/>\n'
    tmp+='\t\t\t<blockValign value="TOP"/>\n'
    tmp+='\t\t</blockTableStyle>\n'
    tmp+='\t\t<initialize>\n'
    tmp+='\t\t\t<paraStyle name="all" alignment="justify"/>\n'
    tmp+='\t\t</initialize>\n'
    #titulo do parágrafo: é por default centralizado
    tmp+='\t\t<paraStyle name="style.Title" fontName="Helvetica" fontSize="11" leading="13" alignment="RIGHT"/>\n'
    tmp+='\t\t<paraStyle name="P1" fontName="Helvetica-Bold" fontSize="12.0" textColor="gray" leading="14" spaceBefore="6" alignment="LEFT"/>\n'
    tmp+='\t\t<paraStyle name="P2" fontName="Helvetica" fontSize="10.0" leading="10" alignment="LEFT"/>\n'
    tmp+='\t\t<paraStyle name="texto_projeto" fontName="Helvetica" fontSize="12.0" leading="12" spaceAfter="10" alignment="JUSTIFY"/>\n'
    tmp+='\t</stylesheet>\n'

    return tmp

def inf_basicas(dic_inf_basicas):
    """
    Função que gera o código rml das funções básicas do relatório
    """

    tmp=''
    #Texto do projeto
    texto_projeto = str(dic_inf_basicas['texto_projeto'])
    if texto_projeto != "" and texto_projeto != None :
        tmp+='\t\t<para style="texto_projeto">' + texto_projeto.replace('&','&amp;') + '</para>\n'

    #inÃ­cio das informações básicas
    tmp+='\t\t<para style="P1">Informações Básicas</para>\n'
    if str(dic_inf_basicas['apresentada']) != "" and str(dic_inf_basicas['apresentada']) != None:
        tmp+='\t\t<para style="P2"><b>Apresentada em: </b> ' + str(dic_inf_basicas['apresentada']) + '</para>\n'

    if str(dic_inf_basicas['formato']) != "" and str(dic_inf_basicas['formato']) != None:
        tmp+='\t\t<para style="P2"><b>Formato: </b> ' + str(dic_inf_basicas['formato']) + '</para>\n'

    if dic_inf_basicas['publicada']==0:
        tmp+='\t\t<para style="P2"><b>Publicada:</b> Não</para>\n'
    else: 
        tmp+='\t\t<para style="P2"><b>Publicada:</b> Sim</para>\n'

    if str(dic_inf_basicas['objeto']) != "" and str(dic_inf_basicas['objeto']) != None:
        tmp+='\t\t<para style="P2"><b>Objeto: </b> ' + str(dic_inf_basicas['objeto']) + '</para>\n'

    if dic_inf_basicas['tramitacao']==0:
        tmp+='\t\t<para style="P2"><b>Tramitação:</b> Não</para>\n'
    else:
        tmp+='\t\t<para style="P2"><b>Tramitação:</b> Sim</para>\n'

    if str(dic_inf_basicas['reg_tramitacao']) != "" and str(dic_inf_basicas['reg_tramitacao']) != None:
        tmp+='\t\t<para style="P2"><b>Regime: </b> ' + str(dic_inf_basicas['reg_tramitacao']) + '</para>\n'

    if str(dic_inf_basicas['prazo']) != "" and str(dic_inf_basicas['prazo']) != None:
        tmp+='\t\t<para style="P2"><b>Dias de prazo: </b> ' + str(dic_inf_basicas['prazo']) + '</para>\n'

    if str(dic_inf_basicas['fim_prazo']) != "" and str(dic_inf_basicas['fim_prazo']) != None:
        tmp+='\t\t<para style="P2"><b>Data do fim do prazo: </b> ' + str(dic_inf_basicas['fim_prazo']) + '</para>\n'

    if dic_inf_basicas['mat_complementar'] == 0:
        tmp+='\t\t<para style="P2"><b>Matéria Complementar:</b> Não</para>\n'
    else:
        tmp+='\t\t<para style="P2"><b>Matéria Complementar:</b> Sim</para>\n'

    if dic_inf_basicas['polemica'] == 0:
        tmp+='\t\t<para style="P2"><b>Polêmica:</b> Não</para>\n'
    else:
        tmp+='\t\t<para style="P2"><b>Polêmica:</b> Sim</para>\n'

    apelido = dic_inf_basicas['apelido']
    if apelido != "" and apelido != None:
        tmp+='\t\t<para style="P2"><b>Apelido: </b> ' + apelido.replace('&','&amp;') + '</para>\n'

    indexacao = dic_inf_basicas['indexacao']
    if indexacao != "" and indexacao != None:
        tmp+='\t\t<para style="P2"><b>Indexação: </b> ' + indexacao.replace('&','&amp;') + '</para>\n'

    observacao = dic_inf_basicas['observacao']
    if observacao != "" and observacao != None:
        tmp+='\t\t<para style="P2"><b>Observação: </b> ' + observacao.replace('&','&amp;') + '</para>\n'

    return tmp

def orig_externa(dic_orig_externa):
    """
    Função que gera o código rml da origem externa
    """

    tmp=''
    tmp+='\t\t<para style="P1">Origem Externa</para>\n'
    try:
        if dic_orig_externa['local'] != "" and dic_orig_externa['local'] != None:
            tmp+='\t\t<para style="P2"><b>Local:</b> ' + dic_orig_externa['local'] + '</para>\n'

        if dic_orig_externa['data'] != "" and dic_orig_externa['data'] != None:
            tmp+='\t\t<para style="P2"><b>Data:</b> ' + dic_orig_externa['data'] + '</para>\n'

        if dic_orig_externa['tipo'] != "" and dic_orig_externa['tipo'] != None:
            tmp+='\t\t<para style="P2"><b>Tipo:</b> ' + dic_orig_externa['tipo'] + '</para>\n'

        if dic_orig_externa['numero_ano'] != "" and dic_orig_externa['numero_ano'] != None:
            tmp+='\t\t<para style="P2"><b>Número/Ano:</b> ' + dic_orig_externa['numero_ano'] + '</para>\n'
    except: pass

    return tmp

def mat_anexadas(lst_mat_anexadas):

    tmp=''
    tmp+='\t\t<para style="P1">Matérias Anexadas</para>\n'
    for dic_mat in  lst_mat_anexadas:
        if dic_mat['nom_mat']!="" and dic_mat['nom_mat']!= None:
            tmp+='\t\t<para style="P2"><b>Nome da matéria:</b> ' + dic_mat['nom_mat'] + '</para>\n'
            tmp+='\t\t<para style="P2"><b>Data:</b> ' + dic_mat['data'] + '</para>\n'
            tmp+='\t\t<para style="P2"><b>Data final:</b> ' + str(dic_mat['data_fim']) + '</para>\n'
    return tmp

def autoria(lst_autoria):

    tmp=''
    tmp+='\t\t<para style="P1">Autores</para>\n'
    for dic_autor in lst_autoria:
        if dic_autor['nom_autor'] != "" and dic_autor['nom_autor'] != None:
            tmp+='\t\t<para style="P2"><b>Nome do Autor:</b> ' + dic_autor['nom_autor'] + '</para>\n'

        if dic_autor['nom_autor'] != "" and dic_autor['cargo'] != None:
            tmp+='\t\t<para style="P2"><b>Cargo:</b> ' + dic_autor['cargo'] + '</para>\n'

        if dic_autor['nom_autor'] != "" and dic_autor['tipo'] != None:
            tmp+='\t\t<para style="P2"><b>Tipo:</b> ' + dic_autor['tipo'] + '</para>\n'
    return tmp

def despachos_iniciais(lst_des_iniciais):

    tmp=''
    tmp+='\t\t<para style="P1">Despachos Iniciais</para>\n'
    for dic_dados in lst_des_iniciais:
        if dic_dados['nom_comissao']==None:
            dic_dados['nom_comissao']=" "
        tmp+='\t\t<para style="P2"><b>Nome da comissão:</b> ' + dic_dados['nom_comissao'] + '</para>\n'
    return tmp

def tramitacoes(dic_tramitacoes):

    tmp=''
    tmp+='\t\t<para style="P1">Última Tramitação</para>\n'
    try:
        tmp+='\t\t<para style="P2"><b>Data Ação:</b> ' + str(dic_tramitacoes['data']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Unidade Local:</b> ' + dic_tramitacoes['unidade'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Encaminhada em:</b> ' + str(dic_tramitacoes['data_enc']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Destino:</b> ' + dic_tramitacoes['destino'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Turno:</b> ' + dic_tramitacoes['turno'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Status:</b> ' + dic_tramitacoes['status'] + '</para>\n'
        if dic_tramitacoes['urgente']==0:
            tmp+='\t\t<para style="P2"><b>Urgente:</b> Não</para>\n'
        else: 
            tmp+='\t\t<para style="P2"><b>Urgente:</b> Sim</para>\n'

        tmp+='\t\t<para style="P2"><b>Data do fim do prazo:</b> ' + str(dic_tramitacoes['data_fim']) + '</para>\n'
        if dic_tramitacoes['texto_acao'] != "" and dic_tramitacoes['texto_acao'] != None :
            tmp+='\t\t<para style="P2"><b>Texto da Ação:</b> ' + dic_tramitacoes['texto_acao'].replace('&','&amp;') + '</para>\n'

    except: pass
    return tmp

def relatorias(lst_relatorias):

    tmp=''
    tmp+='\t\t<para style="P1">Relatorias</para>\n'
    for dic_comissao in lst_relatorias:
        tmp+='\t\t<para style="P2"><b>Comissão:</b> ' + dic_comissao['nom_comissao'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Data Designação:</b> ' + str(dic_comissao['data_desig']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Parlamentar:</b> ' + dic_comissao['parlamentar'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Data Destituição:</b> ' + str(dic_comissao['data_dest']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Motivo Fim Relatoria:</b> ' + dic_comissao['motivo'] + '</para>\n'
    return tmp

def numeracoes(lst_numeracoes):

    tmp=''
    tmp+='\t\t<para style="P1">Numerações</para>\n'
    for dic_dados in lst_numeracoes:
        tmp+='\t\t<para style="P2"><b>Nome:</b> ' + dic_dados['nome'] + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Ano:</b> ' + str(dic_dados['ano']) + '</para>\n'
    return tmp

def legislacoes_citadas(lst_leg_citadas):

    tmp=''
    tmp+='\t\t<para style="P1">Legislações Citadas</para>\n'
    for dic_dados in lst_leg_citadas:
        tmp+='\t\t<para style="P2"><b>Tipo Norma:</b> ' + str(dic_dados['nome_lei']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Disposição:</b> ' + str(dic_dados['disposicao']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Parte:</b> ' + str(dic_dados['parte']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Livro:</b> ' + str(dic_dados['livro']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Tí­tulo:</b> ' + str(dic_dados['titulo']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Capí­tulo:</b> ' + str(dic_dados['capitulo']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Seção:</b> ' + str(dic_dados['secao']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Subseção:</b> ' + str(dic_dados['subsecao']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Artigo:</b> ' + str(dic_dados['artigo']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Parágrafo:</b> ' + str(dic_dados['paragrafo']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Inciso:</b> ' + str(dic_dados['inciso']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Alí­nea:</b> ' + str(dic_dados['alinea']) + '</para>\n'
        tmp+='\t\t<para style="P2"><b>Item:</b> ' + str(dic_dados['item']) + '</para>\n'
    return tmp

def documentos_acessorios(lst_acessorios):

    tmp=''
    tmp+='\t\t<para style="P1">Documentos Acessórios</para>\n'
    for dic_dados in lst_acessorios:
        if dic_dados['tipo']!=None:
            tmp+='\t\t<para style="P2"><b>Tipo:</b> ' + dic_dados['tipo'] + '</para>\n'

        if dic_dados['nome']!=None:
            tmp+='\t\t<para style="P2"><b>Nome:</b> ' + dic_dados['nome'] + '</para>\n'

        tmp+='\t\t<para style="P2"><b>Data:</b> ' + dic_dados['data'] + '</para>\n'
        if dic_dados['autor']!=None:
            tmp+='\t\t<para style="P2"><b>Autor:</b> ' + dic_dados['autor'] + '</para>\n'

        if dic_dados['ementa']!=None:
            tmp+='\t\t<para style="P2"><b>Ementa:</b> ' + dic_dados['ementa'].replace('&','&amp;') + '</para>\n'
        if dic_dados['indexacao']!=None:
            tmp+='\t\t<para style="P2"><b>Ementa:</b> ' + dic_dados['indexacao'].replace('&','&amp;') + '</para>\n'
    return tmp

def principal(imagem, dic_rodape,dic_inf_basicas,dic_orig_externa,lst_mat_anexadas,lst_autoria,lst_des_iniciais,
              dic_tramitacoes,lst_relatorias,lst_numeracoes,lst_leg_citadas,lst_acessorios,sessao=''):
    """
    Função principal responsável por chamar as funções que irão gerar o código rml apropriado
    """

    arquivoPdf=str(int(time.time()*100))+".pdf"

    tmp=''
    tmp+='<?xml version="1.0" encoding="utf-8" standalone="no" ?>\n'
    tmp+='<!DOCTYPE document SYSTEM "rml_1_0.dtd">\n'
    tmp+='<document filename="relatorio.pdf">\n'
    tmp+='\t<template pageSize="(21cm, 29.7cm)" title="Relatorio de Materias" author="Interlegis" allowSplitting="20">\n'
    tmp+='\t\t<pageTemplate id="first">\n'
    tmp+='\t\t\t<pageGraphics>\n'
    tmp+=cabecalho(dic_inf_basicas,imagem)
    tmp+=rodape(dic_rodape)
    tmp+='\t\t\t</pageGraphics>\n'
    tmp+='\t\t\t<frame id="first" x1="2cm" y1="4cm" width="17cm" height="20.5cm"/>\n'
    tmp+='\t\t</pageTemplate>\n'
    tmp+='\t</template>\n'
    tmp+=paraStyle()
    tmp+='\t<story>\n'
    tmp+=inf_basicas(dic_inf_basicas)
    tmp+=orig_externa(dic_orig_externa)
    tmp+=mat_anexadas(lst_mat_anexadas)
    tmp+=autoria(lst_autoria)
    tmp+=despachos_iniciais(lst_des_iniciais)
    tmp+=tramitacoes(dic_tramitacoes)
    tmp+=relatorias(lst_relatorias)
    tmp+=numeracoes(lst_numeracoes)
    tmp+=legislacoes_citadas(lst_leg_citadas)
    tmp+=documentos_acessorios(lst_acessorios)
    tmp+='\t</story>\n'
    tmp+='</document>\n'
    tmp_pdf=parseString(tmp)

    if hasattr(context.temp_folder,arquivoPdf):
        context.temp_folder.manage_delObjects(ids=arquivoPdf)
    context.temp_folder.manage_addFile(arquivoPdf)
    arq=context.temp_folder[arquivoPdf]
    arq.manage_edit(title='Arquivo PDF temporário.',filedata=tmp_pdf,content_type='application/pdf')

#   try:  
#     tmp_pdf=parseString(unicode(tmp, 'utf-8'))  
#   except:  
#     tmp_pdf=parseString(unicode(tmp, 'utf-8'))

    return "/temp_folder/"+arquivoPdf

return principal(imagem, dic_rodape,dic_inf_basicas,dic_orig_externa,lst_mat_anexadas,lst_autoria,lst_des_iniciais,
                 dic_tramitacoes,lst_relatorias,lst_numeracoes,lst_leg_citadas,lst_acessorios,sessao)
