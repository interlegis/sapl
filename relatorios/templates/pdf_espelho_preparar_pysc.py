import os

request=context.REQUEST
response=request.RESPONSE
session= request.SESSION

data=DateTime().strftime('%d/%m/%Y')

#Abaixo é gerada a string para o rodapé da página
casa={}
aux=context.sapl_documentos.props_sapl.propertyItems()
for item in aux:
 casa[item[0]]=item[1]
localidade=context.zsql.localidade_obter_zsql(cod_localidade=casa["cod_localidade"])
if len(casa["num_cep"])==8:
 cep=casa["num_cep"][:4]+"-"+casa["num_cep"][5:]
else:
 cep=""

linha1=casa["end_casa"]
if cep!="":
  if casa["end_casa"]!="" and casa["end_casa"]!=None:
     linha1 = linha1 + " - "
  linha1 = linha1 + "CEP "+cep
if localidade[0].nom_localidade!="" and localidade[0].nom_localidade!=None:
  linha1 = linha1 + " - "+localidade[0].nom_localidade+" "+localidade[0].sgl_uf
if casa["num_tel"]!="" and casa["num_tel"]!=None:
  linha1 = linha1 + " Tel.: "+ casa["num_tel"]

linha2=casa["end_web_casa"]
if casa["end_email_casa"]!="" and casa["end_email_casa"]!=None:
  if casa["end_web_casa"]!="" and casa["end_web_casa"]!=None:
    linha2 = linha2 + " - "
  linha2 =  linha2 + "E-mail: "+casa["end_email_casa"]

data_emissao=DateTime().strftime("%d/%m/%Y")
rodape=[linha1,linha2,data_emissao]

#Por fim, gera-se as entradas para o cabeçalho
estados=context.zsql.localidade_obter_zsql(tip_localidade="u")
for uf in estados:
 if localidade[0].sgl_uf==uf.sgl_uf:
  nom_estado=uf.nom_localidade
  break
cabecalho={}
cabecalho["nom_casa"]=casa["nom_casa"]
cabecalho["nom_estado"]="Estado de "+nom_estado

# tenta buscar o logotipo da casa LOGO_CASA
if hasattr(context.sapl_documentos.props_sapl,'logo_casa.gif'):
  imagem = context.sapl_documentos.props_sapl['logo_casa.gif'].absolute_url()
else:
  imagem = context.sapl_site.sapl_skin.imagens.absolute_url() + "/brasao_transp.gif"

#Verifica o tamanho da lista das materias selecionadas vindas do form
REQUEST=context.REQUEST
if REQUEST.txt_check=='1':
  cod_mat = REQUEST['check_ind']
  materias=[]
  REQUEST=context.REQUEST
  for materia in context.zsql.materia_obter_zsql(cod_materia=cod_mat):
        dic={}
	dic['titulo']="INDICAÃÃO: "+str(materia.num_ident_basica)+" "+str(materia.ano_ident_basica)
	dic['materia']=str(materia.num_ident_basica)+"/"+str(materia.ano_ident_basica)
	dic['dat_apresentacao']=materia.dat_apresentacao
	dic['txt_ementa']=materia.txt_ementa

        dic['nom_autor'] = " "
        for autoria in context.zsql.autoria_obter_zsql(cod_materia=materia.cod_materia, ind_primeiro_autor=1):
            for autor in context.zsql.autor_obter_zsql(cod_autor=autoria.cod_autor):
                if autor.des_tipo_autor=='Parlamentar':
                    for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=autor.cod_parlamentar):
                        dic['nom_autor']=parlamentar.nom_completo
                elif autor.des_tipo_autor=='Comissao':
                    for comissao in context.zsql.comissao_obter_zsql(cod_comissao=autor.cod_comissao):
                        dic['nom_autor']=comissao.nom_comissao
                else:
                    dic['nom_autor']=autor.nom_autor

        des_status = ''
        txt_tramitacao=''
        data_ultima_acao = ''

	dic['localizacao_atual']=" "
        for tramitacao in context.zsql.tramitacao_obter_zsql(cod_materia=materia.cod_materia,ind_ult_tramitacao=1):
            if tramitacao.cod_unid_tram_dest:
                cod_unid_tram = tramitacao.cod_unid_tram_dest
            else:
                cod_unid_tram = tramitacao.cod_unid_tram_local

            for unidade_tramitacao in context.zsql.unidade_tramitacao_obter_zsql(cod_unid_tramitacao = cod_unid_tram):
                if unidade_tramitacao.cod_orgao:
                    dic['localizacao_atual']=unidade_tramitacao.nom_orgao
                elif unidade_tramitacao.cod_parlamentar:
                    dic['localizacao_atual']=unidade_tramitacao.nom_parlamentar
                else:
                    dic['localizacao_atual']=unidade_tramitacao.nom_comissao

            des_status=tramitacao.des_status
            txt_tramitacao=tramitacao.txt_tramitacao
            data_ultima_acao = tramitacao.dat_tramitacao

	dic['des_situacao']=des_status
        dic['ultima_acao']=txt_tramitacao
        dic['data_ultima_acao']=data_ultima_acao

        dic['norma_juridica_vinculada'] = "Não há nenhuma norma jurídica vinculada"
        for norma in context.zsql.materia_buscar_norma_juridica_zsql(cod_materia=materia.cod_materia):
            dic['norma_juridica_vinculada']=norma.des_norma+" "+str(norma.num_norma)+"/"+str(norma.ano_norma)

        materias.append(dic)

else:
  codigo = REQUEST.check_ind
  materias=[]
  REQUEST=context.REQUEST
  for cod_mat in codigo:
   for materia in context.zsql.materia_obter_zsql(cod_materia=cod_mat):
        dic={}
	dic['titulo']="INDICAÃÃO: "+str(materia.num_ident_basica)+" "+str(materia.ano_ident_basica)
        dic['materia']=str(materia.num_ident_basica)+"/"+str(materia.ano_ident_basica)
        dic['dat_apresentacao']=materia.dat_apresentacao
        dic['txt_ementa']=materia.txt_ementa

        dic['nom_autor'] = " " 
        for autoria in context.zsql.autoria_obter_zsql(cod_materia=materia.cod_materia, ind_primeiro_autor=1):
            for autor in context.zsql.autor_obter_zsql(cod_autor=autoria.cod_autor):
                if autor.des_tipo_autor=='Parlamentar':
                    for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=autor.cod_parlamentar):
                        dic['nom_autor']=parlamentar.nom_completo
                elif autor.des_tipo_autor=='Comissao':
                    for comissao in context.zsql.comissao_obter_zsql(cod_comissao=autor.cod_comissao):
                        dic['nom_autor']=comissao.nom_comissao
                else:
                    dic['nom_autor']=autor.nom_autor
            
        des_status = ''
        txt_tramitacao=''
	data_ultima_acao = ''

        dic['localizacao_atual']=" "
        for tramitacao in context.zsql.tramitacao_obter_zsql(cod_materia=materia.cod_materia,ind_ult_tramitacao=1):
	    if tramitacao.cod_unid_tram_dest:
                cod_unid_tram = tramitacao.cod_unid_tram_dest
            else:
                cod_unid_tram = tramitacao.cod_unid_tram_local
            
            for unidade_tramitacao in context.zsql.unidade_tramitacao_obter_zsql(cod_unid_tramitacao = cod_unid_tram):
                if unidade_tramitacao.cod_orgao:
                    dic['localizacao_atual']=unidade_tramitacao.nom_orgao
		elif unidade_tramitacao.cod_parlamentar:
		    dic['localizacao_atual']=unidade_tramitacao.nom_parlamentar
                else:
                    dic['localizacao_atual']=unidade_tramitacao.nom_comissao
        
            des_status=tramitacao.des_status
            txt_tramitacao=tramitacao.txt_tramitacao
	    data_ultima_acao = tramitacao.dat_tramitacao

        dic['des_situacao']=des_status
        dic['ultima_acao']=txt_tramitacao
	dic['data_ultima_acao']=data_ultima_acao

	dic['norma_juridica_vinculada'] = "Não há nenhuma norma jurídica vinculada"
	for norma in context.zsql.materia_buscar_norma_juridica_zsql(cod_materia=materia.cod_materia):
	    dic['norma_juridica_vinculada']=norma.des_norma+" "+str(norma.num_norma)+"/"+str(norma.ano_norma)

        materias.append(dic)

filtro={} # Dicionário que conterá os dados do filtro

# Atribuições diretas do REQUEST
#filtro['data_apres']=REQUEST.data

#filtro['tipo_materia']=''
#for tipo_materia in context.zsql.tipo_materia_legislativa_obter_zsql(ind_excluido=0, tip_materia=9):
#    filtro['tipo_materia']= tipo_materia.sgl_tipo_materia + ' - ' + tipo_materia.des_tipo_materia

#filtro['partido']=''
#if REQUEST.lst_cod_partido!='':
#    for partido in context.zsql.partido_obter_zsql(ind_excluido=0,cod_partido=REQUEST.lst_cod_partido):
#        filtro['partido']=partido.sgl_partido + ' - ' + partido.nom_partido

#filtro['tramitando']=''
#if REQUEST.rad_tramitando=='1':
#    filtro['tramitacao']='Sim'
#elif REQUEST['rad_tramitando']=='0':
#    filtro['tramitacao']='Não'

#filtro['situacao_atual']=''
#if REQUEST.lst_status!='':
#    for status in context.zsql.status_tramitacao_obter_zsql(ind_exluido=0,cod_status=REQUEST.lst_status):
#        filtro['situacao_atual']=status.sgl_status + ' - ' + status.des_status

sessao=session.id
caminho = context.pdf_espelho_gerar(sessao,imagem,data,materias,cabecalho,rodape,filtro)
if caminho=='aviso':
 return response.redirect('mensagem_emitir_proc')
else:
 response.redirect(caminho)
