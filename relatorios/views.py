from datetime import datetime

from django.http import HttpResponse

from base.models import CasaLegislativa
from base.views import ESTADOS
from materia.models import Autoria, MateriaLegislativa, Tramitacao

from .templates import pdf_capa_processo_gerar, pdf_materia_gerar


def get_cabecalho(casa):

    cabecalho = {}
    cabecalho["nom_casa"] = casa.nome
    cabecalho["nom_estado"] = "Estado de " + ESTADOS[casa.uf.upper()]
    return cabecalho


def get_imagem(casa):

    if casa.logotipo:
        return casa.logotipo.path
    else:
        # TODO: recuperar de uma variavel de sistema
        return 'static/img/brasao_transp.gif'


def get_rodape(casa):

    if len(casa.cep) == 8:
        cep = casa.cep[:4] + "-" + casa.cep[5:]
    else:
        cep = ""

    linha1 = casa.endereco

    if cep:
        if casa.endereco:
            linha1 = linha1 + " - "
        linha1 = linha1 + "CEP " + cep

    # substituindo nom_localidade por municipio e sgl_uf por uf
    if casa.municipio:
        linha1 = linha1 + " - " + casa.municipio + " " + casa.uf

    if casa.telefone:
        linha1 = linha1 + " Tel.: " + casa.telefone

    if casa.endereco_web:
        linha2 = casa.endereco_web
    else:
        linha2 = ""

    if casa.email:
        if casa.endereco_web:
            linha2 = linha2 + " - "
        linha2 = linha2 + "E-mail: " + casa.email

    data_emissao = datetime.today().strftime("%d/%m/%Y")

    return [linha1, linha2, data_emissao]


def get_materias(mats):

    materias = []
    for materia in mats:
        dic = {}
        dic['titulo'] = materia.tipo.sigla + " " + materia.tipo.descricao \
            + " " + str(materia.numero) + "/" + str(materia.ano)
        dic['txt_ementa'] = materia.ementa

        autores = Autoria.objects.filter(materia=materia)
        dic['nom_autor'] = " "
        for autoria in autores:
            if autoria.autor.parlamentar:
                dic['nom_autor'] = autoria.autor.parlamentar.nome_completo
            elif autoria.autor.comissao:
                dic['nom_autor'] = autoria.autor.comissao.nome

        des_status = ''
        txt_tramitacao = ''

        dic['localizacao_atual'] = " "

        tramitacoes = Tramitacao.objects.filter(
            unidade_tramitacao_destino__isnull=True).order_by(
            'data_tramitacao')

        for tramitacao in tramitacoes:
            des_status = tramitacao.status.descricao
            txt_tramitacao = tramitacao.texto

        # for tramitacao in context.zsql
        #    .tramitacao_obter_zsql(cod_materia
        #        =materia.cod_materia,ind_ult_tramitacao=1):
        #     if tramitacao.cod_unid_tram_dest:
        #         cod_unid_tram = tramitacao.cod_unid_tram_dest
        #     else:
        #         cod_unid_tram = tramitacao.cod_unid_tram_local
        #     for unidade_tramitacao in
        #         context.zsql
        #              .unidade_tramitacao_obter_zsql(
        #                   cod_unid_tramitacao = cod_unid_tram):
        #         if unidade_tramitacao.cod_orgao:
        #             dic['localizacao_atual']=unidade_tramitacao.nom_orgao
        #         else:
        #             dic['localizacao_atual']=unidade_tramitacao.nom_comissao
        #     des_status=tramitacao.des_status
        #     txt_tramitacao=tramitacao.txt_tramitacao

        dic['des_situacao'] = des_status
        dic['ultima_acao'] = txt_tramitacao

        dic['norma_vinculada'] = " "
        # for norma_vinculada in context.zsql
        #     .materia_buscar_norma_juridica_zsql(cod_materia=materia.cod_materia):
        #     dic['norma_vinculada']=
        #       norma_vinculada.des_norma+" "
        #       +str(norma_vinculada.num_norma)+"/"+str(norma_vinculada.ano_norma)

        materias.append(dic)

    return materias


def relatorio_materia(request):
    '''
        pdf_materia_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)

    # TODO pesquisar baseado em filtros
    mats = MateriaLegislativa.objects.all()[:50]

    materias = get_materias(mats)

    pdf = pdf_materia_gerar.principal(None,
                                      imagem,
                                      None,
                                      materias,
                                      cabecalho,
                                      rodape)

    response.write(pdf)

    return response


def get_processos(prot):
    pass

    # protocolos = []

    # for p in prot:
    #     dic={}
    #     dic['titulo']=str(protocolo.cod_protocolo)
    #     dic['ano']=str(protocolo.ano_protocolo)
    #     dic['data']=context.pysc.iso_to_port_pysc(protocolo.dat_protocolo)+' - '+protocolo.hor_protocolo
    #     dic['txt_assunto']=protocolo.txt_assunto_ementa
    #     dic['txt_interessado']=protocolo.txt_interessado
    #     dic['nom_autor'] = " " 
        # if protocolo.cod_autor!=None:
#            for autor in context.zsql.autor_obter_zsql(cod_autor=protocolo.cod_autor):
#                 if autor.des_tipo_autor=='Parlamentar':
#                     for parlamentar in context.zsql.parlamentar_obter_zsql(cod_parlamentar=autor.cod_parlamentar):
#                         dic['nom_autor']=parlamentar.nom_completo
#                 elif autor.des_tipo_autor=='Comissao':
#                     for comissao in context.zsql.comissao_obter_zsql(cod_comissao=autor.cod_comissao):
#                         dic['nom_autor']=comissao.nom_comissao
#                 else:
#                     dic['nom_autor']=autor.nom_autor
#         else:
#             dic['nom_autor']=protocolo.txt_interessado

#         dic['natureza']=''
#         if protocolo.tip_processo==0:
#            dic['natureza']='Administrativo'
#         if protocolo.tip_processo==1:
#            dic['natureza']='Legislativo'
  
#         dic['ident_processo']=protocolo.des_tipo_materia or protocolo.des_tipo_documento

#         dic['sgl_processo']=protocolo.sgl_tipo_materia or protocolo.sgl_tipo_documento

#         dic['num_materia']=''
#         for materia in context.zsql.materia_obter_zsql(num_protocolo=protocolo.cod_protocolo,ano_ident_basica=protocolo.ano_protocolo):
#                dic['num_materia']=str(materia.num_ident_basica)+'/'+ str(materia.ano_ident_basica)

#         dic['num_documento']=''
#         for documento in context.zsql.documento_administrativo_obter_zsql(num_protocolo=protocolo.cod_protocolo):
#                dic['num_documento']=str(documento.num_documento)+'/'+ str(documento.ano_documento)

#         dic['num_processo']=dic['num_materia'] or dic['num_documento']

#         dic['numeracao']=''
#         for materia_num in context.zsql.materia_obter_zsql(num_protocolo=protocolo.cod_protocolo,ano_ident_basica=protocolo.ano_protocolo):
#            for numera in context.zsql.numeracao_obter_zsql(cod_materia=materia_num.cod_materia,ind_excluido=0):
#                dic['numeracao']='PROCESSO N&#176; ' +str(numera.num_materia)+'/'+ str(numera.ano_materia)

#         dic['anulado']=''
#         if protocolo.ind_anulado==1:
#            dic['anulado']='Nulo'

#         protocolos.append(dic)


def relatorio_processo(request):
    '''
        pdf_capa_processo_gerar.py
    '''

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="somefilename.pdf"'

    casa = CasaLegislativa.objects.first()

    cabecalho = get_cabecalho(casa)
    rodape = get_rodape(casa)
    imagem = get_imagem(casa)



    protocolos = get_processo(protocolos)

    pdf = pdf_materia_gerar.principal(None,
                                      imagem,
                                      None,
                                      protocolos,
                                      cabecalho,
                                      rodape)

    response.write(pdf)

    return response    
