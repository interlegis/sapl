"""
Gravação de arquivos enviados ao SAPL (MEDIA_ROOT).

Quando o disco enche ou o diretório de mídia perde a permissão de escrita,
o ``FileSystemStorage`` do Django levanta um ``OSError`` genérico, que vira
um erro 500 sem explicação, e deixa no disco o pedaço do arquivo que chegou a
ser gravado. Este módulo:

- remove o arquivo parcial e converte o erro em ``FalhaGravacaoArquivo``;
- descreve a falha em uma mensagem que o usuário e o suporte entendem, usada
  pelo ``FalhaGravacaoArquivoMiddleware`` na interface e na API.
"""
import errno
import logging
import os

from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)

# Sem espaço no disco ou cota do usuário esgotada.
ERRNOS_ESPACO = frozenset((errno.ENOSPC, errno.EDQUOT))

# Diretório sem permissão de escrita ou montado como somente leitura.
ERRNOS_PERMISSAO = frozenset((errno.EACCES, errno.EPERM, errno.EROFS))


class FalhaGravacaoArquivo(OSError):
    """O arquivo enviado não pôde ser gravado no armazenamento do SAPL."""


def falha_de_gravacao(exception):
    """
    Indica se a exceção é uma falha de gravação de arquivo que merece uma
    resposta própria. Além das falhas do armazenamento, inclui a falta de
    espaço ao gravar o arquivo temporário do upload, que acontece antes de
    o arquivo chegar ao armazenamento.
    """
    if isinstance(exception, FalhaGravacaoArquivo):
        return True
    return isinstance(exception, OSError) and \
        exception.errno in ERRNOS_ESPACO


def sem_espaco(exception):
    return getattr(exception, 'errno', None) in ERRNOS_ESPACO


def mensagem_falha_gravacao(exception):
    """Mensagem para o usuário, sem caminhos nem detalhes do servidor."""
    codigo = getattr(exception, 'errno', None)
    if codigo in ERRNOS_ESPACO:
        motivo = 'o espaço de armazenamento do servidor está esgotado'
    elif codigo in ERRNOS_PERMISSAO:
        motivo = 'o servidor está sem permissão de escrita no diretório ' \
                 'de arquivos'
    else:
        motivo = 'ocorreu um erro no armazenamento do servidor'
    return ('Não foi possível gravar o arquivo enviado: {}. O arquivo não '
            'foi salvo. Informe o suporte técnico do SAPL e confira o '
            'registro antes de tentar novamente.').format(motivo)


class ArmazenamentoArquivos(FileSystemStorage):
    """
    ``FileSystemStorage`` que não deixa arquivo parcial no disco e identifica
    as falhas de gravação com ``FalhaGravacaoArquivo``.

    É o armazenamento padrão do SAPL (``DEFAULT_FILE_STORAGE``).
    """

    def save(self, name, content, max_length=None):
        try:
            return super().save(name, content, max_length=max_length)
        except FalhaGravacaoArquivo:
            raise
        except OSError as e:
            raise FalhaGravacaoArquivo(e.errno, e.strerror, name) from e

    def _save(self, name, content):
        # save() acabou de escolher um nome livre: se ele já existe, o
        # arquivo não é desta gravação e não pode ser removido.
        caminho = self.path(name)
        ja_existia = os.path.lexists(caminho)
        try:
            return super()._save(name, content)
        except OSError as e:
            if not ja_existia:
                self._remove_arquivo_parcial(caminho)
            raise FalhaGravacaoArquivo(e.errno, e.strerror, name) from e

    @staticmethod
    def _remove_arquivo_parcial(caminho):
        """
        Remove o que foi gravado antes da falha. Um arquivo truncado ocupa o
        espaço que ainda restava e, se ficasse, impediria até a gravação de
        arquivos pequenos.
        """
        try:
            os.remove(caminho)
        except FileNotFoundError:
            pass
        except OSError as e:
            logger.error('Não foi possível remover o arquivo parcial "{}" '
                         '({}).'.format(caminho, e))
