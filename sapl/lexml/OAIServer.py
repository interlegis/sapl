from datetime import datetime

import oaipmh
import oaipmh.error
import oaipmh.metadata
import oaipmh.server
from django.urls import reverse
from lxml import etree
from lxml.builder import ElementMaker

from sapl.base.models import AppConfig, CasaLegislativa
from sapl.lexml.models import LexmlPublicador
from sapl.norma.models import NormaJuridica


class OAILEXML:
    """
        Padrao OAI do LeXML
        Esta registrado sobre o nome 'oai_lexml'
    """

    def __init__(self, prefix):
        self.prefix = prefix
        self.ns = {'oai_lexml': 'http://www.lexml.gov.br/oai_lexml', }
        self.schemas = {'oai_lexml': 'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd'}

    def __call__(self, element, metadata):
        data = metadata.record
        value = etree.XML(data['metadata'])
        element.append(value)


class OAIServer:
    """
        An OAI-2.0 compliant oai server.
        Underlying code is based on pyoai's oaipmh.server'
    """

    XSI_NS = 'http://www.w3.org/2001/XMLSchema-instance'
    ns = {'lexml': 'http://www.lexml.gov.br/oai_lexml'}
    schema = {'oai_lexml': 'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd'}

    def __init__(self, config={}):
        self.config = config

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

    def create_header_and_metadata(self, record):
        header = self.create_header(record)
        metadata = oaipmh.common.Metadata(None, record['metadata'])
        metadata.record = record
        return header, metadata

    def list_query(self, from_date=None, until_date=None, offset=0, batch_size=10, identifier=None):
        if identifier:
            identifier = int(identifier.split('/')[-1])  # Get internal id
        else:
            identifier = ''
        until_date = datetime.now() if not until_date or until_date > datetime.now() else until_date
        return self.oai_query(offset=offset, batch_size=batch_size, from_date=from_date, until_date=until_date,
                              identifier=identifier)

    def check_metadata_prefix(self, metadata_prefix):
        if not metadata_prefix in self.config['metadata_prefixes']:
            raise oaipmh.error.CannotDisseminateFormatError

    def listRecords(self, metadataPrefix, from_date=None, until_date=None, cursor=0, batch_size=10):
        self.check_metadata_prefix(metadataPrefix)
        for record in self.list_query(from_date, until_date, cursor, batch_size):
            header, metadata = self.create_header_and_metadata(record)
            yield header, metadata, None  # None?

    def get_oai_id(self, internal_id):
        return "oai:{}".format(internal_id)

    def create_header(self, record):
        oai_id = self.get_oai_id(record['record']['id'])
        timestamp = record['record']['when_modified']
        timestamp = timestamp.replace(tzinfo=None)
        sets = []
        deleted = record['record']['deleted']
        return oaipmh.common.Header(None, oai_id, timestamp, sets, deleted)

    def get_esfera_federacao(self):
        appconfig = AppConfig.objects.first()
        return appconfig.esfera_federacao

    def recupera_norma(self, offset, batch_size, from_date, until_date, identifier, esfera):
        kwargs = {'data__lte': until_date}
        if from_date:
            kwargs['data__gte'] = from_date
        if identifier:
            kwargs['numero'] = identifier
        if esfera:
            kwargs['esfera_federacao'] = esfera
        return NormaJuridica.objects.select_related('tipo').filter(**kwargs)[offset:offset + batch_size]

    def monta_id(self, norma):
        if norma:
            num = len(casa.endereco_web.split('.'))
            dominio = '.'.join(casa.endereco_web.split('.')[1:num])
            prefixo_oai = '{}.{}:sapl/'.format(casa.sigla.lower(), dominio)
            numero_interno = norma.numero
            tipo_norma = norma.tipo.equivalente_lexml
            ano_norma = norma.ano
            identificador = '{}{};{};{}'.format(prefixo_oai, tipo_norma, ano_norma, numero_interno)
            return identificador
        else:
            return None

    def monta_urn(self, norma, esfera):
        if norma:
            urn = 'urn:lex:br;'
            esferas = {'M': 'municipal', 'E': 'estadual'}
            municipio = casa.municipio.lower()
            uf = casa.uf.lower()
            for x in [' ', '.de.', '.da.', '.das.', '.do.', '.dos.']:
                municipio = municipio.replace(x, '.')
                uf = uf.replace(x, '.')
            if esfera == 'M':
                urn += '{};{}:'.format(uf, municipio)
                if norma.tipo.equivalente_lexml == 'regimento.interno' or norma.tipo.equivalente_lexml == 'resolucao':
                    urn += 'camara.'
                urn += esferas[esfera] + ':'
            elif esfera == 'E':
                urn += '{}:{}:'.format(uf, esferas[esfera])
            else:
                urn += ':'
            if norma.tipo.equivalente_lexml:
                urn += '{}:{};'.format(norma.tipo.equivalente_lexml, norma.data.isoformat())
            else:
                urn += '{};'.format(norma.data.isoformat())
            if norma.tipo.equivalente_lexml == 'lei.organica' or norma.tipo.equivalente_lexml == 'constituicao':
                urn += norma.ano
            else:
                urn += norma.numero
            if norma.data_vigencia and norma.data_publicacao:
                urn += '@{};publicacao;{}'.format(norma.data_vigencia.isoformat(), norma.data_publicacao.isoformat())
            elif norma.data_publicacao:
                urn += '@inicio.vigencia;publicacao;{}'.format(norma.data_publicacao.isoformat())
            return urn
        else:
            return None

    def data_por_extenso(self, data):
        data = data.strftime('%d-%m-%Y')
        if data != '':
            meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho',
                     8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
            return '{} de {} de {}'.format(data[0:2], meses[int(data[3:5])], data[6:])
        else:
            return ''

    def monta_xml(self, urn, norma):
        publicador = LexmlPublicador.objects.first()
        if norma and publicador:
            LEXML = ElementMaker(namespace=self.ns['lexml'], nsmap=self.ns)
            oai_lexml = LEXML.LexML()
            oai_lexml.attrib['{{}}schemaLocation'.format(self.XSI_NS)] = '{} {}'.format(
                'http://www.lexml.gov.br/oai_lexml', 'http://projeto.lexml.gov.br/esquemas/oai_lexml.xsd')
            texto_integral = norma.texto_integral
            mime_types = {'doc': 'application/msword',
                          'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'odt': 'application/vnd.oasis.opendocument.text',
                          'pdf': 'application/pdf',
                          'rtf': 'application/rtf'}
            if texto_integral:
                url_conteudo = self.config['base_url'] + texto_integral.url
                extensao = texto_integral.url.split('.')[-1]
                formato = mime_types.get(extensao, 'application/octet-stream')
            else:
                formato = 'text/html'
                url_conteudo = self.config['base_url'] + reverse('sapl.norma:normajuridica_detail',
                                                                 kwargs={'pk': norma.numero})
            element_maker = ElementMaker()
            id_publicador = str(publicador.id_publicador)
            item_conteudo = element_maker.Item(url_conteudo, formato=formato, idPublicador=id_publicador,
                                               tipo='conteudo')
            oai_lexml.append(item_conteudo)
            url = self.config['base_url'] + reverse('sapl.norma:normajuridica_detail', kwargs={'pk': norma.numero})
            item_metadado = element_maker.Item(url, formato='text/html', idPublicador=id_publicador, tipo='metadado')
            oai_lexml.append(item_metadado)
            documento_individual = element_maker.DocumentoIndividual(urn)
            oai_lexml.append(documento_individual)
            if norma.tipo.equivalente_lexml == 'lei.organica':
                epigrafe = '{} de {} - {}, de {}'.format(norma.tipo.descricao, casa.municipio,
                                                         casa.uf, norma.ano)
            elif norma.tipo.equivalente_lexml == 'constituicao':
                epigrafe = '{} do Estado de {}, de {}'.format(norma.tipo.descricao, casa.municipio,
                                                              norma.ano)
            else:
                epigrafe = '{} n° {}, de {}'.format(norma.tipo.descricao, norma.numero,
                                                    self.data_por_extenso(norma.data))
            oai_lexml.append(element_maker.Epigrafe(epigrafe))
            oai_lexml.append(element_maker.Ementa(norma.ementa))
            indexacao = norma.indexacao
            if indexacao:
                oai_lexml.append(element_maker.Indexacao(indexacao))
            return etree.tostring(oai_lexml)
        else:
            return None

    def oai_query(self, offset=0, batch_size=10, from_date=None, until_date=None, identifier=None):
        esfera = self.get_esfera_federacao()
        offset = 0 if offset < 0 else offset
        batch_size = 10 if batch_size < 0 else batch_size
        until_date = datetime.now() if not until_date or until_date > datetime.now() else until_date
        normas = self.recupera_norma(offset, batch_size, from_date, until_date, identifier, esfera)
        for norma in normas:
            resultado = {}
            identificador = self.monta_id(norma)
            urn = self.monta_urn(norma, esfera)
            xml_lexml = self.monta_xml(urn, norma)
            resultado['tx_metadado_xml'] = xml_lexml
            resultado['cd_status'] = 'N'
            resultado['id'] = identificador
            resultado['when_modified'] = norma.timestamp
            resultado['deleted'] = 0
            yield {'record': resultado,
                   'metadata': resultado['tx_metadado_xml']}


def OAIServerFactory(config={}):
    """
        Create a new OAI batching OAI Server given a config and a database
    """
    for prefix in config['metadata_prefixes']:
        metadata_registry = oaipmh.metadata.MetadataRegistry()
        metadata_registry.registerWriter(prefix, OAILEXML(prefix))
    return oaipmh.server.BatchingServer(
        OAIServer(config),
        metadata_registry=metadata_registry,
        resumption_batch_size=config['batch_size']
    )


casa = None


def casa_legislativa():
    global casa
    if not casa:
        casa = CasaLegislativa.objects.first()
    return casa if casa else CasaLegislativa()  # retorna objeto dummy


def get_config(url, batch_size):
    config = {'content_type': None,
              'delay': 0,
              'base_asset_path': None,
              'metadata_prefixes': ['oai_lexml']}
    config.update({'titulo': casa_legislativa().nome,  # Inicializa variável global casa
                   'email': casa.email,
                   'base_url': url[:url.find('/', 8)],
                   'descricao': casa.informacao_geral,
                   'batch_size': batch_size})
    return config


if __name__ == '__main__':
    """
        Para executar localmente (estando no diretório raiz):
        
        $ ./manage.py shell_plus
        
        Executar comando        
        %run sapl/lexml/OAIServer.py
    """
    oai_server = OAIServerFactory(get_config('http://127.0.0.1:8000/', 10))
    r = oai_server.handleRequest({'verb': 'ListRecords',
                                  'metadataPrefix': 'oai_lexml'})
    print(r.decode('UTF-8'))
