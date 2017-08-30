import os

request = context.REQUEST
response = request.RESPONSE
session = request.SESSION
if context.REQUEST['cod_sessao_plen'] != '':
    cod_sessao_plen = context.REQUEST['cod_sessao_plen']
    splen = []  # lista contendo as sessões plenárias na data indicada
    pauta = []  # lista contendo a pauta da ordem do dia a ser impressa
    data = ""
    for dat_sessao in context.zsql.sessao_plenaria_obter_zsql(cod_sessao_plen=cod_sessao_plen, ind_excluido=0):
        # converte data para formato yyyy/mm/dd
        data = context.pysc.data_converter_pysc(dat_sessao.dat_inicio_sessao)
        dat_ordem = context.pysc.data_converter_pysc(
            dat_sessao.dat_inicio_sessao)  # converte data para formato yyyy/mm/dd
    # seleciona dados da sessão plenária
    for sp in context.zsql.sessao_plenaria_obter_zsql(dat_inicio_sessao=data, ind_excluido=0):
        dicsp = {}  # dicionário que armazenará os dados a serem impressos de uma sessão plenária
        ts = context.zsql.tipo_sessao_plenaria_obter_zsql(
            tip_sessao=sp.tip_sessao)[0]
        dicsp["sessao"] = str(sp.num_sessao_plen) + "ª Sessao " + ts.nom_sessao + " da " + str(
            sp.num_sessao_leg) + "ª Sessao Legislativa da " + str(sp.num_legislatura) + "ª Legislatura"
        dia = context.pysc.data_converter_por_extenso_pysc(
            data=sp.dat_inicio_sessao)
        hora = context.pysc.hora_formatar_pysc(hora=sp.hr_inicio_sessao)
        dicsp["datasessao"] = "Dia " + \
            str(dia) + " (" + str(sp.dia_sessao) + ") - Inicio as " + hora
        splen.append(dicsp)
        # seleciona as matérias que compõem a pauta na data escolhida
    for ordem in context.zsql.ordem_dia_obter_zsql(dat_ordem=data, ind_excluido=0):
        # seleciona os detalhes de uma matéria
        materia = context.zsql.materia_obter_zsql(
            cod_materia=ordem.cod_materia)[0]
        dic = {}  # dicionário que armazenará os dados a serem impressos de uma matéria
        dic["num_ordem"] = ordem.num_ordem
        dic["id_materia"] = materia.des_tipo_materia + " - Nº " + \
            str(materia.num_ident_basica) + "/" + str(materia.ano_ident_basica)
        # dic["id_materia"] = materia.sgl_tipo_materia+" - "+str(materia.num_ident_basica)+"/"+str(materia.ano_ident_basica)+" - "+materia.des_tipo_materia
        dic["txt_ementa"] = ordem.txt_observacao
        # numeracao do processo 26/02/2011
        dic["des_numeracao"] = ""
        numeracao = context.zsql.numeracao_obter_zsql(
            cod_materia=ordem.cod_materia)
        if len(numeracao):
            numeracao = numeracao[0]
            dic["des_numeracao"] = str(
                numeracao.num_materia) + "/" + str(numeracao.ano_materia)
        dic["des_turno"] = ""
        dic["des_situacao"] = ""
        tramitacao = context.zsql.tramitacao_obter_zsql(
            cod_materia=ordem.cod_materia, ind_ult_tramitacao=1)
        if len(tramitacao):
            tramitacao = tramitacao[0]
            if tramitacao.sgl_turno != "":
                for turno in [("P", "Primeiro"), ("S", "Segundo"), ("U", "Único"), ("L", "Suplementar"), ("A", "Votação Única em Regime de Urgência"), ("B", "1ª Votação"), ("C", "2ª e 3ª Votações")]:
                    if tramitacao.sgl_turno == turno[0]:
                        dic["des_turno"] = turno[1]

            dic["des_situacao"] = tramitacao.des_status
            if dic["des_situacao"] == None:
                dic["des_situacao"] = " "

        dic["nom_autor"] = ''
        autoria = context.zsql.autoria_obter_zsql(
            cod_materia=ordem.cod_materia, ind_primeiro_autor=1)
        if len(autoria):  # se existe autor
            autoria = autoria[0]
        try:
            autor = context.zsql.autor_obter_zsql(cod_autor=autoria.cod_autor)
            if len(autor):
                autor = autor[0]

            if autor.des_tipo_autor == "Parlamentar":
                parlamentar = context.zsql.parlamentar_obter_zsql(
                    cod_parlamentar=autor.cod_parlamentar)[0]
                dic["nom_autor"] = parlamentar.nom_parlamentar

            elif autor.des_tipo_autor == "Comissao":
                comissao = context.zsql.comissao_obter_zsql(
                    cod_comissao=autor.cod_comissao)[0]
                dic["nom_autor"] = comissao.nom_comissao
            else:
                dic["nom_autor"] = autor.nom_autor
        except:
            pass
        lst_relator = []  # lista contendo os relatores da matéria
        for relatoria in context.zsql.relatoria_obter_zsql(cod_materia=ordem.cod_materia):
            parlamentar = context.zsql.parlamentar_obter_zsql(
                cod_parlamentar=relatoria.cod_parlamentar)[0]
            comissao = context.zsql.comissao_obter_zsql(
                cod_comissao=relatoria.cod_comissao)[0]
            lst_relator.append(parlamentar.nom_parlamentar +
                               " - " + comissao.nom_comissao)
        if not len(lst_relator):
            lst_relator = ['']
        dic["lst_relator"] = lst_relator

        # adiciona o dicionário na pauta
        pauta.append(dic)

    # obtém as propriedades da casa legislativa para montar o cabeçalho e o
    # rodapé da página
    casa = {}
    aux = context.sapl_documentos.props_sapl.propertyItems()
    for item in aux:
        casa[item[0]] = item[1]

    # obtém a localidade
    localidade = context.zsql.localidade_obter_zsql(
        cod_localidade=casa["cod_localidade"])

    # monta o cabeçalho da página
    cabecalho = {}
    estado = context.zsql.localidade_obter_zsql(tip_localidade="U")
    for uf in estado:
        if localidade[0].sgl_uf == uf.sgl_uf:
            nom_estado = uf.nom_localidade
            break

    cabecalho["nom_casa"] = casa["nom_casa"]
    cabecalho["nom_estado"] = "Estado do " + nom_estado

    # tenta buscar o logotipo da casa LOGO_CASA
    if hasattr(context.sapl_documentos.props_sapl, 'logo_casa.gif'):
        imagem = context.sapl_documentos.props_sapl[
            'logo_casa.gif'].absolute_url()
    else:
        imagem = context.imagens.absolute_url() + "/brasao_transp.gif"

    # monta o rodapé da página
    num_cep = casa["num_cep"]
    if len(casa["num_cep"]) == 8:
        num_cep = casa["num_cep"][:4] + "-" + casa["num_cep"][5:]

    linha1 = casa["end_casa"]
    if num_cep != None and num_cep != "":
        if casa["end_casa"] != "" and casa["end_casa"] != None:
            linha1 = linha1 + "  "
        linha1 = linha1 + " CEP: " + num_cep
    if localidade[0].nom_localidade != None and localidade[0].nom_localidade != "":
        linha1 = linha1 + "   " + \
            localidade[0].nom_localidade + " - " + localidade[0].sgl_uf
    if casa["num_tel"] != None and casa["num_tel"] != "":
        linha1 = linha1 + "   Tel.: " + casa["num_tel"]

    linha2 = casa["end_web_casa"]
    if casa["end_email_casa"] != None and casa["end_email_casa"] != "":
        if casa["end_web_casa"] != "" and casa["end_web_casa"] != None:
            linha2 = linha2 + " - "
        linha2 = linha2 + "E-mail: " + casa["end_email_casa"]
    dat_emissao = DateTime().strftime("%d/%m/%Y")
    rodape = [linha1, linha2, dat_emissao]

    sessao = session.id
    caminho = context.pdf_ordem_dia_gerar(
        sessao, imagem, dat_ordem, splen, pauta, cabecalho, rodape)
    if caminho == 'aviso':
        return response.redirect('mensagem_emitir_proc')
    else:
        response.redirect(caminho)
