"""
Envio da pauta da sessão plenária a um painel de votação externo.

A Casa liga o envio e informa URL e chave em Configurações da Aplicação.
O SAPL entrega a pauta quando o operador decide; o painel implementa o
recebimento conforme docs/painel-externo.md.
"""
from collections import namedtuple
import logging

from django.urls import reverse
from django.utils.translation import gettext as _
import requests

from sapl.base.models import AppConfig
from sapl.materia.models import Tramitacao
from sapl.sessao.models import ExpedienteMateria, OrdemDia


logger = logging.getLogger(__name__)

TIMEOUT = 15

ResultadoEnvio = namedtuple('ResultadoEnvio', 'ok status_remoto mensagem')


def integracao_ativa():
    return bool(AppConfig.attr('painel_externo_ativo'))


def montar_pauta(sessao, request):
    data_ref = sessao.data_fim or sessao.data_inicio

    def itens(model):
        return (model.objects
                .filter(sessao_plenaria=sessao)
                .select_related('materia__tipo')
                .prefetch_related('materia__autores'))

    return {
        'sessao': sessao.pk,
        'sessao_nome': str(sessao),
        'tipo_sessao': {'id': sessao.tipo_id, 'nome': sessao.tipo.nome},
        'expediente': [
            {'materia': _materia(item, data_ref, request)}
            for item in itens(ExpedienteMateria)],
        'ordem_dia': [
            {'numero_ordem': item.numero_ordem,
             'materia': _materia(item, data_ref, request)}
            for item in itens(OrdemDia)],
    }


def enviar_pauta(sessao, request):
    url = AppConfig.attr('painel_externo_url')
    pauta = montar_pauta(sessao, request)

    try:
        resposta = requests.post(
            url, json=pauta, timeout=TIMEOUT,
            headers={'X-API-KEY': AppConfig.attr('painel_externo_api_key')})
    except requests.RequestException:
        logger.exception('Falha ao enviar a pauta da sessão %s ao painel '
                         'externo em %s.', sessao.pk, url)
        return ResultadoEnvio(
            False, None, _('Não foi possível conectar ao painel externo.'))

    logger.info('Pauta da sessão %s enviada ao painel externo por %s: '
                'HTTP %s.', sessao.pk, request.user, resposta.status_code)
    return ResultadoEnvio(
        resposta.ok, resposta.status_code, _mensagem_do_painel(resposta))


def _materia(item, data_ref, request):
    m = item.materia
    status_tramitacao, fase_materia = _tramitacao(m, data_ref)
    status_sessao = _status_na_sessao(item)

    return {
        'id_materia': m.pk,
        'nome_documento': str(m),
        'autoria': [{'id': a.id, 'nome': a.nome} for a in m.autores.all()],
        'tipo_materia': {'id': m.tipo_id, 'nome': m.tipo.descricao},
        'ementa': m.ementa,
        'status': status_sessao,
        'status_sessao': status_sessao,
        'status_tramitacao': status_tramitacao,
        'fase_materia': fase_materia,
        'quorum': m.tipo.quorum_minimo_votacao,
        'tipo_votacao': item.get_tipo_votacao_display(),
        'pdf_url': _pdf_url(m, request),
        'tramitacao_pdf_url': request.build_absolute_uri(reverse(
            'sapl.relatorios:relatorio_materia_tramitacao',
            kwargs={'pk': m.pk})),
    }


def _status_na_sessao(item):
    registro = item.registrovotacao_set.filter(materia=item.materia).first()
    if registro:
        return registro.tipo_resultado_votacao.nome
    if item.retiradapauta_set.filter(materia=item.materia).exists():
        return 'Retirado'
    if item.registroleitura_set.filter(materia=item.materia).exists():
        return 'Leitura'
    return ''


def _tramitacao(materia, data_ref):
    tramitacao = (Tramitacao.objects
                  .filter(materia=materia, data_tramitacao__lte=data_ref)
                  .order_by('-data_tramitacao', '-id')
                  .select_related('status')
                  .first())
    if not tramitacao:
        return '', ''
    status = tramitacao.status.descricao if tramitacao.status else ''
    fase = tramitacao.get_turno_display() if tramitacao.turno else ''
    return status, fase


def _pdf_url(materia, request):
    """Texto original ou, na falta dele, os acessórios em PDF reunidos."""
    if materia.texto_original:
        return request.build_absolute_uri(materia.texto_original.url)
    if materia.documentoacessorio_set.filter(
            arquivo__iendswith='pdf').exists():
        return request.build_absolute_uri(reverse(
            'sapl.materia:merge_docacessorios',
            kwargs={'pk': materia.pk}))
    return None


def _mensagem_do_painel(resposta):
    try:
        corpo = resposta.json()
    except ValueError:
        return ''
    if not isinstance(corpo, dict):
        return ''
    return str(corpo.get('message') or corpo.get('detail') or '')
