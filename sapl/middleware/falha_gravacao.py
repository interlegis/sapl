import logging

from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils.html import escape

from sapl.armazenamento import (falha_de_gravacao, mensagem_falha_gravacao,
                                sem_espaco)

logger = logging.getLogger(__name__)

# 507 Insufficient Storage (RFC 4918): o servidor não tem espaço para
# guardar o que foi enviado. As demais falhas de gravação são do servidor.
STATUS_SEM_ESPACO = 507
STATUS_FALHA = 500


class FalhaGravacaoArquivoMiddleware:
    """
    Responde com uma mensagem clara, na interface e na API, quando um arquivo
    enviado não pode ser gravado (disco cheio, cota esgotada, diretório sem
    permissão de escrita), em vez do erro 500 genérico. O traceback vai para
    o log com o id da requisição, que também aparece na resposta para o
    usuário informar ao suporte.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not falha_de_gravacao(exception):
            return None

        request_id = getattr(request, 'request_id', '')
        username = getattr(getattr(request, 'user', None), 'username', '')
        logger.error('user={}. Falha ao gravar arquivo enviado em {} {}: {}'
                     .format(username, request.method, request.path,
                             exception),
                     exc_info=exception)

        mensagem = mensagem_falha_gravacao(exception)
        status = STATUS_SEM_ESPACO if sem_espaco(exception) else STATUS_FALHA

        if self.resposta_json(request):
            return JsonResponse({'detail': mensagem,
                                 'request_id': request_id},
                                status=status)

        contexto = {'mensagem': mensagem, 'request_id': request_id}
        try:
            conteudo = render_to_string('falha_gravacao_arquivo.html',
                                        contexto, request=request)
        except Exception:
            logger.exception('Erro ao renderizar a página de falha de '
                             'gravação de arquivo.')
            conteudo = '<p>{}</p><p>Código da requisição: {}</p>'.format(
                escape(mensagem), escape(request_id))
        return HttpResponse(conteudo, status=status)

    @staticmethod
    def resposta_json(request):
        return request.path_info.startswith('/api/') or \
            'application/json' in request.META.get('HTTP_ACCEPT', '')
