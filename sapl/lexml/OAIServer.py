
import os
import re
from datetime import datetime

import oaipmh
import oaipmh.metadata
import oaipmh.server
import oaipmh.error

from lxml import etree
from lxml.builder import ElementMaker


class OAILEXML():
    """
        Padrao OAI do LeXML
        Esta registrado sobre o nome 'oai_lexml'
    """

    def __init__(self, prefix):
        self.prefix = prefix
        self.ns = {'oai_lexml': 'http://www.lexml.gov.br/oai_lexml',}
        self.schemas = {'oai_lexml': 'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd'}   

    def get_namespace(self):
        return self.ns[self.prefix]

    def get_schema_location(self):
        return self.schemas[self.prefix]

    # utilizado?????
    def __call__(self, element, metadata):
        data = metadata.record
        value = etree.XML(data['metadata'])
        element.append(value)


class OAIServer():
    """An OAI-2.0 compliant oai server.
    
    Underlying code is based on pyoai's oaipmh.server'
    """

    XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
    ns = {'lexml': 'http://www.lexml.gov.br/oai_lexml'}
    schema = {'oai_lexml': 'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd'}    
    
    def __init__(self, config={}):
        self.config = config

    def get_oai_id(self, internal_id):
        return "oai:{}".format(internal_id)

    # verificar
    def get_internal_id(self, oai_id):
        return int(oai_id.split('/').pop())

    def get_internal_set_id(self, oai_setspec_id):
        return oai_setspec_id[4:]

    # # utilizado?
    # def get_asset_path(self, internal_id, asset):
    #     return os.path.abspath(
    #         os.path.join(self.base_asset_path,
    #                      internal_id,
    #                      asset['filename']))

    # aparentemente nao utilizado
    def identify(self):
        result = oaipmh.common.Identify(
            repositoryName=self.config['titulo'],
            baseURL=self.config['base_url'],
            protocolVersion='2.0',
            adminEmails=self.config['email'],
            earliestDatestamp=datetime(2001, 1, 1, 10, 00),
            deletedRecord='transient',
            granularity='YYYY-MM-DDThh:mm:ssZ',
            compression=['identity'],
            toolkit_description=False)
        if not self.config['descricao']:
            result.add_description(self.config['descricao'])
        return result

    def get_writer(self, prefix):
        return OAILEXML(prefix)

    # utilizado?
    def listMetadataFormats(self, identifier=None):
        result = []
        for prefix in self.config['metadata_prefixes']:
            writer = self.get_writer(prefix)
            ns = writer.get_namespace()
            schema = writer.get_schema_location()
            result.append((prefix, schema, ns))
        return result


    def listRecords(self, metadataPrefix, set=None, from_=None, until=None, cursor=0, batch_size=10):
        self.check_metadata_prefix(metadataPrefix)
        for record in self.list_query(set, from_, until, cursor, batch_size):
            header, metadata = self.create_header_and_metadata(record)
            yield header, metadata, None # NONE?????

    def create_header(self, record):
        oai_id = self.get_oai_id(record['record']['id'])
        timestamp = record['record']['when_modified']
        sets = []
        deleted = record['record']['deleted']
        return oaipmh.common.Header(oai_id, timestamp, sets, deleted)


    def listIdentifiers(self, metadata_prefix, dataset=None,
                         start=None, end=None, cursor=0, batch_size=10):
        self.check_metadata_prefix(metadata_prefix)
        for record in self.list_query(dataset, start, end, cursor, batch_size):
            yield self.create_header(record)

    def getRecord(self, metadata_prefix, identifier):
        header = None
        metadata = None       
        self.check_metadata_prefix(metadata_prefix)
        for record in self.list_query(identifier=identifier):
            header, metadata = self.create_header_and_metadata(record)

        # pega o ultimo header??????
        if not header:
            raise oaipmh.error.IdDoesNotExistError(identifier)
        return header, metadata, None

    def check_metadata_prefix(self, metadata_prefix):
        if not metadata_prefix in self.config['metadata_prefixes']:
            raise oaipmh.error.CannotDisseminateFormatError

    def create_header_and_metadata(self, record):
        header = self.create_header(record)
        metadata = oaipmh.common.Metadata(record['metadata'])
        metadata.record = record
        return header, metadata
    
    def list_query(self, dataset=None, from_=None, until=None, 
                   cursor=0, batch_size=10, identifier=None):

        if identifier:
            identifier = self.get_internal_id(identifier)
        else:
            identifier = ''
        if dataset:
            dataset = self.get_internal_set_id(dataset)
        
        # TODO: verificar se a data eh UTC
        now = datetime.now()
        # until nunca deve ser no futuro
        if not until or until > now:
            until = now
            
        return self.oai_query(offset=cursor,
                              batch_size=batch_size,
                              from_date=from_,
                              until_date=until,
                              identifier=identifier)

    def get_nome_casa(self):
        # TODO: recuperar do BD
        return "Casa de teste"

    def verifica_esfera_federacao(self):
        """ Funcao para verificar a esfera da federacao
        """
        nome_camara = self.get_nome_casa()
        camara = [u'Câmara','Camara','camara',u'camara']
        assembleia = [u'Assembléia','Assembleia','assembleia',u'assembléia']

        # TODO: pegar espera de forma mais inteligente
        if [tipo for tipo in camara if nome_camara.startswith(tipo)]:
            return 'M'
        elif [tipo for tipo in assembleia if nome_camara.startswith(tipo)]:
            return 'E'
        else:
            return ''

    def monta_id(self,cod_norma):
        ''' Funcao que monta o id do objeto do LexML
        '''

        #consultas
        consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)
        if consulta:
            consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)[0]
            
            end_web_casa = self.sapl_documentos.props_sapl.end_web_casa
            sgl_casa = self.sapl_documentos.props_sapl.sgl_casa.lower()
            num = len(end_web_casa.split('.'))
            dominio = '.'.join(end_web_casa.split('.')[1:num])
            
            prefixo_oai = '%s.%s:sapl/' % (sgl_casa,dominio)
            numero_interno = consulta.num_norma
            tipo_norma = consulta.voc_lexml
            ano_norma = consulta.ano_norma
            
            identificador = '%s%s;%s;%s' % (prefixo_oai,tipo_norma,ano_norma,numero_interno)
        
            return identificador
        else:
            return None
        
    def monta_urn(self, cod_norma):
        ''' Funcao que monta a URN do LexML
        '''

        esfera = self.verifica_esfera_federacao()
        consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)
        if consulta:
            consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)[0]
            url = self.portal_url() + '/consultas/norma_juridica/norma_juridica_mostrar_proc?cod_norma=' + str(cod_norma)
            urn='urn:lex:br;'
            esferas = {'M':'municipal','E':'estadual'}
            
            localidade = self.zsql.localidade_obter_zsql(cod_localidade = self.sapl_documentos.props_sapl.cod_localidade)
            municipio = localidade[0].nom_localidade_pesq.lower()
            for i in re.findall('\s',municipio):
                municipio = municipio.replace(i, '.')
            
            # solucao temporaria
            if re.search( '\.de\.', municipio):
                municipio = [municipio.replace(i, '.') for i in re.findall( '\.de\.', municipio)][0]
            if re.search( '\.da\.', municipio):
                municipio = [municipio.replace(i, '.') for i in re.findall( '\.da\.', municipio)][0]
            if re.search( '\.das\.', municipio):
                municipio = [municipio.replace(i, '.') for i in re.findall( '\.das\.', municipio)][0]
            if re.search( '\.do\.', municipio):
                municipio = [municipio.replace(i, '.') for i in re.findall( '\.do\.', municipio)][0]
            if re.search( '\.dos\.', municipio):
                municipio = [municipio.replace(i, '.') for i in re.findall( '\.dos\.', municipio)][0]

            sigla_uf=localidade[0].sgl_uf
            uf = self.zsql.localidade_obter_zsql(sgl_uf=sigla_uf,tip_localidade='U')[0].nom_localidade_pesq.lower()
            for i in re.findall('\s',uf):
                uf = uf.replace(i, '.')
            
            # solucao temporaria
            if re.search( '\.de\.', uf):
                uf = [uf.replace(i, '.') for i in re.findall( '\.de\.', uf)][0]
            if re.search( '\.da\.', uf):
                uf = [uf.replace(i, '.') for i in re.findall( '\.da\.', uf)][0]
            if re.search( '\.das\.', uf):
                uf = [uf.replace(i, '.') for i in re.findall( '\.das\.', uf)][0]
            if re.search( '\.do\.', uf):
                uf = [uf.replace(i, '.') for i in re.findall( '\.do\.', uf)][0]
            if re.search( '\.dos\.', uf):
                uf = [uf.replace(i, '.') for i in re.findall( '\.dos\.', uf)][0]

            if self.verifica_esfera_federacao() == 'M':
                urn += uf + ';'
                urn += municipio + ':'
            elif self.verifica_esfera_federacao() == 'E':
                urn += uf + ':'

            if esfera == 'M':
                if consulta.voc_lexml == 'regimento.interno' or consulta.voc_lexml == 'resolucao':
                    urn += 'camara.municipal:'
                else:
                    urn += esferas[esfera] + ':'
            else:
                urn += esferas[esfera] + ':'

            urn += consulta.voc_lexml + ':'

            urn += self.pysc.port_to_iso_pysc(consulta.dat_norma) + ';'

            if consulta.voc_lexml == 'lei.organica' or consulta.voc_lexml == 'constituicao':
                urn += consulta.ano_norma
            else:
                urn += consulta.num_norma

            if consulta.dat_vigencia and consulta.dat_publicacao:
                urn += '@'
                urn += self.pysc.port_to_iso_pysc(consulta.dat_vigencia)
                urn += ';publicacao;'
                urn += self.pysc.port_to_iso_pysc(consulta.dat_publicacao)
            elif consulta.dat_publicacao:
                urn += '@'
                urn += 'inicio.vigencia;publicacao;' + self.pysc.port_to_iso_pysc(consulta.dat_publicacao)
#            else:
#                urn += 'inicio.vigencia;publicacao;'
#                
#            if consulta.dat_publicacao:
#                urn += self.pysc.port_to_iso_pysc(consulta.dat_publicacao)
                
            return urn
        else:
            return None

    def oai_query(self, offset=0, batch_size=20,
                  from_date=None, until_date=None, identifier=None):

        esfera = self.verifica_esfera_federacao()

        batch_size = 0 if batch_size < 0 else batch_size    

        # garante que a data 'until'(ate) esteja setada, e nao no futuro
        if not until_date or until_date > datetime.now():
            until_date = datetime.now()

        if not from_date:
            from_date = ''

        normas = self.zsql.lexml_normas_juridicas_obter_zsql(from_date=from_date,
                                                             until_date=until_date,
                                                             offset=offset,
                                                             batch_size=batch_size,
                                                             num_norma=identifier,
                                                             tip_esfera_federacao=esfera)
        for norma in normas:
            resultado = {}            
            cod_norma = norma.cod_norma
            identificador = self.monta_id(cod_norma)
            urn = self.monta_urn(cod_norma)
            xml_lexml = self.monta_xml(urn,cod_norma)
            
            resultado['tx_metadado_xml'] = xml_lexml
            #resultado['id_registro_item'] = resultado['name']
            #del resultado['name']
            #record['sets'] = record['sets'].strip().split(' ')
            #if resultado['sets'] == [u'']:
            #    resultado['sets'] = []
            resultado['cd_status'] = 'N'
            resultado['id'] = identificador
            resultado['when_modified'] = norma.timestamp
            resultado['deleted'] = 0
            if norma.ind_excluido == 1:
                resultado['deleted'] = 1
#                resultado['cd_status'] = 'D'
            yield {'record': resultado,
#                   'sets': ['person'],
                   'metadata': resultado['tx_metadado_xml'],
#                   'assets':{}
                   }

    def monta_xml(self,urn,cod_norma):
        #criacao do xml

        # consultas
        consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)
        publicador = self.zsql.lexml_publicador_obter_zsql()
        if consulta and publicador:
            consulta = self.zsql.lexml_normas_juridicas_obter_zsql(cod_norma=cod_norma)[0]
            publicador = self.zsql.lexml_publicador_obter_zsql()[0]
        
            url = self.portal_url() + '/consultas/norma_juridica/norma_juridica_mostrar_proc?cod_norma=' + str(cod_norma)
            
            E = ElementMaker()
            LEXML = ElementMaker(namespace=self.ns['lexml'],nsmap=self.ns)
            
            oai_lexml = LEXML.LexML()
            
            oai_lexml.attrib['{%s}schemaLocation' % self.XSI_NS] = '%s %s' % (
                        'http://www.lexml.gov.br/oai_lexml',
                        'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd')
            
            id_publicador = str(publicador.id_publicador)

            # montagem da epigrafe
            localidade = self.zsql.localidade_obter_zsql(cod_localidade = self.sapl_documentos.props_sapl.cod_localidade)[0].nom_localidade
            sigla_uf = self.zsql.localidade_obter_zsql(cod_localidade = self.sapl_documentos.props_sapl.cod_localidade)[0].sgl_uf
            if consulta.voc_lexml == 'lei.organica':
                epigrafe = u'%s de %s - %s, de %s' % (consulta.des_tipo_norma, localidade,sigla_uf, consulta.ano_norma)
            elif consulta.voc_lexml == 'constituicao':
                epigrafe = u'%s do Estado de %s, de %s' % (consulta.des_tipo_norma, localidade, consulta.ano_norma)
            else:
                epigrafe = u'%s n° %s,  de %s' % (consulta.des_tipo_norma, consulta.num_norma, self.pysc.data_converter_por_extenso_pysc(consulta.dat_norma))
            
            ementa = consulta.txt_ementa
            
            indexacao = consulta.txt_indexacao
            
            formato = 'text/html'
            id_documento = u'%s_%s' % (str(cod_norma), self.sapl_documentos.norma_juridica.nom_documento)
            if hasattr(self.sapl_documentos.norma_juridica,id_documento):
                arquivo = getattr(self.sapl_documentos.norma_juridica,id_documento) 
                url_conteudo = arquivo.absolute_url()
                formato = arquivo.content_type
                if formato == 'application/octet-stream':
                    formato = 'application/msword'
                if formato == 'image/ipeg':
                    formato = 'image/jpeg'
            
            else:
                url_conteudo = self.portal_url() + '/consultas/norma_juridica/norma_juridica_mostrar_proc?cod_norma=' + str(cod_norma)
            
            item_conteudo = E.Item(url_conteudo,formato=formato, idPublicador=id_publicador,tipo='conteudo')
            oai_lexml.append(item_conteudo)
            
            item_metadado = E.Item(url,formato='text/html', idPublicador=id_publicador,tipo='metadado')
            oai_lexml.append(item_metadado)
            
            documento_individual = E.DocumentoIndividual(urn)
            oai_lexml.append(documento_individual)
            oai_lexml.append(E.Epigrafe(epigrafe.decode('iso-8859-1')))
            oai_lexml.append(E.Ementa(ementa.decode('iso-8859-1')))
            if indexacao:
                oai_lexml.append(E.Indexacao(indexacao.decode('iso-8859-1')))
            return etree.tostring(oai_lexml)
        else:
            return None


def OAIServerFactory(config={}):
    """Create a new OAI batching OAI Server given a config and
    a database"""
    for prefix in config['metadata_prefixes']:
        metadata_registry = oaipmh.metadata.MetadataRegistry()
        metadata_registry.registerWriter(prefix, OAILEXML(prefix))
            
    return oaipmh.server.BatchingServer(
        OAIServer(config),
        metadata_registry=metadata_registry,
        resumption_batch_size=config['batch_size']
        )

# TODO: RECUPERAR DA BASE DE DADOS
def config():
    config = {}
    config['titulo'] = 'cocalzinho' # self.get_nome_repositorio()
    config['email'] = 'camara@cocalzinho.gov' # self.get_email()
    config['base_url'] = 'wwww.aleluia.com' # self.get_base_url()
    config['metadata_prefixes'] = ['oai_lexml',]
    config['descricao'] = 'ficticia' # self.get_descricao_casa()
    config['batch_size'] = 10 # self.get_batch_size()
    config['content_type'] = None,
    config['delay'] = 0,
    config['base_asset_path']=None
    return config

if __name__ == '__main__':
    oai_server = OAIServerFactory(config())
    r = oai_server.handleRequest({'verb':'ListRecords',
                                  'metadataPrefix':'oai_lexml'
                                  })
    print(r)
