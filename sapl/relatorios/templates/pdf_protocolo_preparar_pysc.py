import os

request = context.REQUEST
response = request.RESPONSE
session = request.SESSION

data = DateTime().strftime('%d/%m/%Y')

# Abaixo é gerada a string para o rodapé da página
casa = {}
aux = context.sapl_documentos.props_sapl.propertyItems()
for item in aux:
    casa[item[0]] = item[1]
localidade = context.zsql.localidade_obter_zsql(
    cod_localidade=casa["cod_localidade"])
if len(casa["num_cep"]) == 8:
    cep = casa["num_cep"][:4] + "-" + casa["num_cep"][5:]
else:
    cep = ""

linha1 = casa["end_casa"]
if cep != "":
    if casa["end_casa"] != "" and casa["end_casa"] != None:
        linha1 = linha1 + " - "
    linha1 = linha1 + "CEP " + cep
if localidade[0].nom_localidade != "" and localidade[0].nom_localidade != None:
    linha1 = linha1 + " - " + \
        localidade[0].nom_localidade + " " + localidade[0].sgl_uf
if casa["num_tel"] != "" and casa["num_tel"] != None:
    linha1 = linha1 + " Tel.: " + casa["num_tel"]

linha2 = casa["end_web_casa"]
if casa["end_email_casa"] != "" and casa["end_email_casa"] != None:
    if casa["end_web_casa"] != "" and casa["end_web_casa"] != None:
        linha2 = linha2 + " - "
    linha2 = linha2 + "E-mail: " + casa["end_email_casa"]

data_emissao = DateTime().strftime("%d/%m/%Y")
rodape = [linha1, linha2, data_emissao]

# Por fim, gera-se as entradas para o cabeçalho
estados = context.zsql.localidade_obter_zsql(tip_localidade="u")
for uf in estados:
    if localidade[0].sgl_uf == uf.sgl_uf:
        nom_estado = uf.nom_localidade
        break
cabecalho = {}
cabecalho["nom_casa"] = casa["nom_casa"]
cabecalho["nom_estado"] = "Estado de " + nom_estado

# tenta buscar o logotipo da casa LOGO_CASA
if hasattr(context.sapl_documentos.props_sapl, 'logo_casa.gif'):
    imagem = context.sapl_documentos.props_sapl['logo_casa.gif'].absolute_url()
else:
    imagem = context.imagens.absolute_url() + "/brasao_transp.gif"

# Por fim, utiliza o PythonScript para pesquisar os protocolos e gerar os dados

protocolos = []
REQUEST = context.REQUEST
for protocolo in context.zsql.protocolo_pesquisar_zsql(tip_protocolo=REQUEST['rad_tip_protocolo'],
                                                       cod_protocolo=REQUEST['txt_num_protocolo'], ano_protocolo=REQUEST[
                                                           'txt_ano_protocolo'],
                                                       tip_documento=REQUEST['lst_tip_documento'], tip_processo=REQUEST[
                                                           'rad_tip_processo'],
                                                       tip_materia=REQUEST[
                                                           'lst_tip_materia'], des_assunto=REQUEST['txt_assunto'],
                                                       cod_autor=REQUEST['hdn_cod_autor'], des_interessado=REQUEST[
    'txa_txt_interessado'],
        dat_apres=REQUEST['dt_apres'], dat_apres2=REQUEST['dt_apres2']):
    dic = {}

    dic['titulo'] = str(protocolo.cod_protocolo) + '/' + \
        str(protocolo.ano_protocolo)

    dic['data'] = context.pysc.iso_to_port_pysc(
        protocolo.dat_protocolo) + ' - <b>Horário:</b>' + protocolo.hor_protocolo

    dic['txt_assunto'] = protocolo.txt_assunto_ementa

    dic['txt_interessado'] = protocolo.txt_interessado

    dic['nom_autor'] = " "
    if protocolo.cod_autor != None:
        for autor in context.zsql.autor_obter_zsql(cod_autor=protocolo.cod_autor):
            if autor.des_tipo_autor == 'Parlamentar':
                for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=autor.cod_parlamentar):
                    dic['nom_autor'] = parlamentar.nom_completo
            elif autor.des_tipo_autor == 'Comissao':
                for comissao in context.zsql.comissao_obter_zsql(cod_comissao=autor.cod_comissao):
                    dic['nom_autor'] = comissao.nom_comissao
            else:
                dic['nom_autor'] = autor.nom_autor

    dic['natureza'] = ''
    if protocolo.tip_processo == 0:
        dic['natureza'] = 'Administrativo'
    if protocolo.tip_processo == 1:
        dic['natureza'] = 'Legislativo'

    dic['processo'] = protocolo.des_tipo_materia or protocolo.des_tipo_documento

    dic['anulado'] = ''
    if protocolo.ind_anulado == 1:
        dic['anulado'] = 'Nulo'

    protocolos.append(dic)

filtro = {}  # Dicionário que conterá os dados do filtro

# Atribuições diretas do REQUEST
filtro['numero'] = REQUEST.txt_num_protocolo
filtro['ano'] = REQUEST.txt_ano_protocolo
filtro['tipo_protocolo'] = REQUEST.rad_tip_protocolo
filtro['tipo_processo'] = REQUEST.rad_tip_processo
filtro['assunto'] = REQUEST.txt_assunto
filtro['autor'] = REQUEST.hdn_cod_autor
filtro['interessado'] = REQUEST.txa_txt_interessado

sessao = session.id
caminho = context.pdf_protocolo_gerar(
    sessao, imagem, data, protocolos, cabecalho, rodape, filtro)
if caminho == 'aviso':
    return response.redirect('mensagem_emitir_proc')
else:
    response.redirect(caminho)
