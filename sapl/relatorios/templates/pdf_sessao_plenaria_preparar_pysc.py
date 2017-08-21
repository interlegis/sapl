import os

request = context.REQUEST
response = request.RESPONSE
session = request.SESSION

if context.REQUEST['data'] != '':
    dat_inicio_sessao = context.REQUEST['data']
    pauta = []  # lista contendo a pauta da ordem do dia a ser impressa
    # converte data para formato yyyy/mm/dd
    data = context.pysc.data_converter_pysc(dat_inicio_sessao)
    codigo = context.REQUEST['cod_sessao_plen']

    # seleciona as matérias que compõem a pauta na data escolhida
    for sessao in context.zsql.sessao_plenaria_obter_zsql(dat_inicio_sessao=data, cod_sessao_plen=codigo, ind_excluido=0):
        inf_basicas_dic = {}  # dicionário que armazenará as informacoes basicas da sessao plenaria
        # seleciona o tipo da sessao plenaria
        tipo_sessao = context.zsql.tipo_sessao_plenaria_obter_zsql(
            tip_sessao=sessao.tip_sessao, ind_excluido=0)[0]
        inf_basicas_dic["num_sessao_plen"] = sessao.num_sessao_plen
        inf_basicas_dic["nom_sessao"] = tipo_sessao.nom_sessao
        inf_basicas_dic["num_legislatura"] = sessao.num_legislatura
        inf_basicas_dic["num_sessao_leg"] = sessao.num_sessao_leg
        inf_basicas_dic["dat_inicio_sessao"] = sessao.dat_inicio_sessao
        inf_basicas_dic["hr_inicio_sessao"] = sessao.hr_inicio_sessao
        inf_basicas_dic["dat_fim_sessao"] = sessao.dat_fim_sessao
        inf_basicas_dic["hr_fim_sessao"] = sessao.hr_fim_sessao

        # Lista da composicao da mesa diretora
        lst_mesa = []
        for composicao in context.zsql.composicao_mesa_sessao_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):
            for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=composicao.cod_parlamentar, ind_excluido=0):
                for cargo in context.zsql.cargo_mesa_obter_zsql(cod_cargo=composicao.cod_cargo, ind_excluido=0):
                    dic_mesa = {}
                    dic_mesa['nom_parlamentar'] = parlamentar.nom_parlamentar
                    dic_mesa['sgl_partido'] = parlamentar.sgl_partido
                    dic_mesa['des_cargo'] = cargo.des_cargo
                    lst_mesa.append(dic_mesa)

        # Lista de presença na sessão
        lst_presenca_sessao = []
        for presenca in context.zsql.presenca_sessao_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):
            for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=presenca.cod_parlamentar, ind_excluido=0):
                dic_presenca = {}
                dic_presenca["nom_parlamentar"] = parlamentar.nom_parlamentar
                dic_presenca['sgl_partido'] = parlamentar.sgl_partido
                lst_presenca_sessao.append(dic_presenca)

        # Exibe os Expedientes
        lst_expedientes = []
        dic_expedientes = None
        for tip_expediente in context.zsql.tipo_expediente_obter_zsql():
            for expediente in context.zsql.expediente_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, cod_expediente=tip_expediente.cod_expediente, ind_excluido=0):
                dic_expedientes = {}
                dic_expedientes[
                    "nom_expediente"] = tip_expediente.nom_expediente
                dic_expedientes["txt_expediente"] = expediente.txt_expediente

            if dic_expedientes:
                lst_expedientes.append(dic_expedientes)

        # Lista das matérias do Expediente, incluindo o resultado das votacoes
        lst_expediente_materia = []
        for expediente_materia in context.zsql.votacao_expediente_materia_obter_zsql(dat_ordem=data, cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):

            # seleciona os detalhes de uma matéria
            materia = context.zsql.materia_obter_zsql(
                cod_materia=expediente_materia.cod_materia)[0]

            dic_expediente_materia = {}
            dic_expediente_materia["num_ordem"] = expediente_materia.num_ordem
            dic_expediente_materia["id_materia"] = materia.sgl_tipo_materia + " " + materia.des_tipo_materia + \
                " " + str(materia.num_ident_basica) + "/" + \
                str(materia.ano_ident_basica)
            dic_expediente_materia["des_numeracao"] = ""

            numeracao = context.zsql.numeracao_obter_zsql(
                cod_materia=expediente_materia.cod_materia)
            if len(numeracao):
                numeracao = numeracao[0]
                dic_expediente_materia["des_numeracao"] = str(
                    numeracao.num_materia) + "/" + str(numeracao.ano_materia)

            tram = context.zsql.tramitacao_turno_obter_zsql(
                cod_materia=materia.cod_materia, dat_inicio_sessao=data)
            dic_expediente_materia["des_turno"] = ""
            if len(tram):
                tram_turno = tram[0]
                if tram_turno.sgl_turno != "":
                    for turno in [("P", "Primeiro"), ("S", "Segundo"), ("U", "Único"), ("L", "Suplementar"), ("A", "Votação Única em Regime de Urgência"), ("B", "1ª Votação"), ("C", "2ª e 3ª Votações"), ("F", "Final")]:
                        if tram_turno.sgl_turno == turno[0]:
                            dic_expediente_materia["des_turno"] = turno[1]

            dic_expediente_materia["txt_ementa"] = materia.txt_ementa
            dic_expediente_materia[
                "ordem_observacao"] = expediente_materia.ordem_observacao
            dic_expediente_materia["nom_autor"] = ""
            autoria = context.zsql.autoria_obter_zsql(
                cod_materia=expediente_materia.cod_materia, ind_primeiro_autor=1)
            if len(autoria) > 0:  # se existe autor
                autoria = autoria[0]
                autor = context.zsql.autor_obter_zsql(
                    cod_autor=autoria.cod_autor)
                if len(autor) > 0:
                    autor = autor[0]
                    try:
                        if autor.des_tipo_autor == "Parlamentar":
                            parlamentar = context.zsql.parlamentar_obter_zsql(
                                cod_parlamentar=autor.cod_parlamentar)[0]
                            dic_expediente_materia[
                                "nom_autor"] = parlamentar.nom_parlamentar
                        elif autor.des_tipo_autor == "Comissao":
                            comissao = context.zsql.comissao_obter_zsql(
                                cod_comissao=autor.cod_comissao)[0]
                            dic_expediente_materia[
                                "nom_autor"] = comissao.nom_comissao
                        elif autor.nom_autor != "":
                            dic_expediente_materia[
                                "nom_autor"] = autor.nom_autor
                        else:
                            dic_expediente_materia[
                                "nom_autor"] = autor.des_tipo_autor
                    except:
                        dic_expediente_materia["nom_autor"] = "NC-em"

            dic_expediente_materia["votacao_observacao"] = ""
            if expediente_materia.tip_resultado_votacao:
                resultado = context.zsql.tipo_resultado_votacao_obter_zsql(
                    tip_resultado_votacao=expediente_materia.tip_resultado_votacao, ind_excluido=0)
                for i in resultado:
                    dic_expediente_materia["nom_resultado"] = i.nom_resultado
                    if expediente_materia.votacao_observacao:
                        dic_expediente_materia[
                            "votacao_observacao"] = expediente_materia.votacao_observacao
            else:
                dic_expediente_materia["nom_resultado"] = "Matéria não votada"
                dic_expediente_materia["votacao_observacao"] = "Vazio"
            lst_expediente_materia.append(dic_expediente_materia)

        # Lista dos oradores do Expediente
        lst_oradores_expediente = []
        for orador_expediente in context.zsql.oradores_expediente_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):
            for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=orador_expediente.cod_parlamentar, ind_excluido=0):
                dic_oradores_expediente = {}
                dic_oradores_expediente[
                    "num_ordem"] = orador_expediente.num_ordem
                dic_oradores_expediente[
                    "nom_parlamentar"] = parlamentar.nom_parlamentar
                dic_oradores_expediente[
                    'sgl_partido'] = parlamentar.sgl_partido
                lst_oradores_expediente.append(dic_oradores_expediente)

        # Lista presença na ordem do dia
        lst_presenca_ordem_dia = []
        for presenca_ordem_dia in context.zsql.presenca_ordem_dia_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):
            for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=presenca_ordem_dia.cod_parlamentar, ind_excluido=0):
                dic_presenca_ordem_dia = {}
                dic_presenca_ordem_dia[
                    'nom_parlamentar'] = parlamentar.nom_parlamentar
                dic_presenca_ordem_dia['sgl_partido'] = parlamentar.sgl_partido
                lst_presenca_ordem_dia.append(dic_presenca_ordem_dia)

        # Lista das matérias da Ordem do Dia, incluindo o resultado das
        # votacoes
        lst_votacao = []
        for votacao in context.zsql.votacao_ordem_dia_obter_zsql(dat_ordem=data, cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):

            # seleciona os detalhes de uma matéria
            materia = context.zsql.materia_obter_zsql(
                cod_materia=votacao.cod_materia)[0]

            dic_votacao = {}
            dic_votacao["num_ordem"] = votacao.num_ordem
            dic_votacao["id_materia"] = materia.sgl_tipo_materia + " " + materia.des_tipo_materia + \
                " " + str(materia.num_ident_basica) + "/" + \
                str(materia.ano_ident_basica)
            dic_votacao["des_numeracao"] = ""
            numeracao = context.zsql.numeracao_obter_zsql(
                cod_materia=votacao.cod_materia)
            if len(numeracao):
                numeracao = numeracao[0]
                dic_votacao["des_numeracao"] = str(
                    numeracao.num_materia) + "/" + str(numeracao.ano_materia)
            dic_votacao["des_turno"] = ""
            tramitacao = context.zsql.tramitacao_obter_zsql(
                cod_materia=materia.cod_materia, ind_ult_tramitacao=1)
            if len(tramitacao):
                tramitacao = tramitacao[0]
            tram = context.zsql.tramitacao_turno_obter_zsql(
                cod_materia=materia.cod_materia, dat_inicio_sessao=data)
            if len(tram):
                tram_turno = tram[0]
                if tram_turno.sgl_turno != "":
                    for turno in [("P", "Primeiro"), ("S", "Segundo"), ("U", "Único"), ("L", "Suplementar"), ("F", "Final"), ("A", "Votação Única em Regime de Urgência"), ("B", "1ª Votação"), ("C", "2ª e 3ª Votações")]:
                        if tram_turno.sgl_turno == turno[0]:
                            dic_votacao["des_turno"] = turno[1]
            dic_votacao["txt_ementa"] = materia.txt_ementa
            dic_votacao["ordem_observacao"] = votacao.ordem_observacao
            dic_votacao["nom_autor"] = ""
            autoria = context.zsql.autoria_obter_zsql(
                cod_materia=votacao.cod_materia, ind_primeiro_autor=1)
            if len(autoria) > 0:  # se existe autor
                autoria = autoria[0]
                autor = context.zsql.autor_obter_zsql(
                    cod_autor=autoria.cod_autor)
                if len(autor) > 0:
                    autor = autor[0]
                    try:
                        if autor.des_tipo_autor == "Parlamentar":
                            parlamentar = context.zsql.parlamentar_obter_zsql(
                                cod_parlamentar=autor.cod_parlamentar)[0]
                            dic_votacao[
                                "nom_autor"] = parlamentar.nom_parlamentar
                        elif autor.des_tipo_autor == "Comissao":
                            comissao = context.zsql.comissao_obter_zsql(
                                cod_comissao=autor.cod_comissao)[0]
                            dic_votacao["nom_autor"] = comissao.nom_comissao
                        elif autor.nom_autor != "":
                            dic_votacao["nom_autor"] = autor.nom_autor
                        else:
                            dic_votacao["nom_autor"] = autor.des_tipo_autor
                    except:
                        dic_votacao["nom_autor"] = "NC-od"

            dic_votacao["votacao_observacao"] = ""
            if votacao.tip_resultado_votacao:
                resultado = context.zsql.tipo_resultado_votacao_obter_zsql(
                    tip_resultado_votacao=votacao.tip_resultado_votacao, ind_excluido=0)
                for i in resultado:
                    dic_votacao["nom_resultado"] = i.nom_resultado
                    if votacao.votacao_observacao:
                        dic_votacao[
                            "votacao_observacao"] = votacao.votacao_observacao
            else:
                dic_votacao["nom_resultado"] = "Matéria não votada"
                dic_votacao["votacao_observacao"] = "Vazio"
            lst_votacao.append(dic_votacao)

        # Lista dos oradores nas Explicações Pessoais
        lst_oradores = []
        for orador in context.zsql.oradores_obter_zsql(cod_sessao_plen=sessao.cod_sessao_plen, ind_excluido=0):
            for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=orador.cod_parlamentar, ind_excluido=0):
                dic_oradores = {}
                dic_oradores["num_ordem"] = orador.num_ordem
                dic_oradores["nom_parlamentar"] = parlamentar.nom_parlamentar
                dic_oradores['sgl_partido'] = parlamentar.sgl_partido
                lst_oradores.append(dic_oradores)

    # obtém as propriedades da casa legislativa para montar o cabeçalho e o
    # rodapé da página
    cabecalho = {}

    # tenta buscar o logotipo da casa LOGO_CASA
    if hasattr(context.sapl_documentos.props_sapl, 'logo_casa.gif'):
        imagem = context.sapl_documentos.props_sapl[
            'logo_casa.gif'].absolute_url()
    else:
        imagem = context.imagens.absolute_url() + "/brasao_transp.gif"

    # Abaixo é gerado o dic do rodapé da página (linha 7)
    casa = {}
    aux = context.sapl_documentos.props_sapl.propertyItems()
    for item in aux:
        casa[item[0]] = item[1]
    localidade = context.zsql.localidade_obter_zsql(
        cod_localidade=casa["cod_localidade"])
    data_emissao = DateTime().strftime("%d/%m/%Y")
    rodape = casa
    rodape['data_emissao'] = data_emissao

    inf_basicas_dic['nom_camara'] = casa['nom_casa']
    REQUEST = context.REQUEST
    for local in context.zsql.localidade_obter_zsql(cod_localidade=casa['cod_localidade']):
        rodape['nom_localidade'] = "   " + local.nom_localidade
        rodape['sgl_uf'] = local.sgl_uf

#    return lst_votacao
    sessao = session.id
    caminho = context.pdf_sessao_plenaria_gerar(rodape, sessao, imagem, inf_basicas_dic, lst_mesa, lst_presenca_sessao,
                                                lst_expedientes, lst_expediente_materia, lst_oradores_expediente, lst_presenca_ordem_dia, lst_votacao, lst_oradores)
    if caminho == 'aviso':
        return response.redirect('mensagem_emitir_proc')
    else:
        response.redirect(caminho)
