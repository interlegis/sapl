Data de atualização do conteúdo público
======================================

O cabeçalho informa a última alteração identificada no conteúdo público do
SAPL. A data é global: uma alteração em uma norma pode aparecer também na
página de matérias. Ela não comprova a atualidade de cada seção nem, por si
só, o atendimento integral aos critérios do PNTP.

Inclusões, alterações, exclusões e mudanças de visibilidade de conteúdo
público atualizam o indicador. Login, consultas, estatísticas de acesso e
alterações exclusivamente em dados privados não o atualizam. O serviço
``sapl.base.atualizacao`` mantém o registro dos modelos elegíveis e os campos
excluídos. Novos fluxos de gravação em lote nesses modelos devem usar
``bulk_create_public``, ``bulk_update_public`` ou ``update_public``: os métodos
originais do Django não emitem sinais de gravação.

Na inicialização da aplicação, os métodos ``save`` e ``delete`` dos modelos
registrados são envolvidos em transações, preservando os métodos existentes.
Assim, uma falha na gravação do indicador também desfaz a alteração no banco.
Para presenças com conflito de chave única, o helper usa ``get_or_create``:
reenviar uma presença já existente não avança a data.

Uma sessão futura, não iniciada e sem pauta publicada só contribui quando
se torna pública. O sistema guarda a data original da alteração e a data
prevista da sessão. A leitura do cabeçalho não grava nem gera timestamps.

Implantação
-----------

Após aplicar as migrações, conferir as evidências antes de inicializar::

    python manage.py inicializar_atualizacao_publica --dry-run
    python manage.py inicializar_atualizacao_publica

O comando aceita ``--database`` e pode ser reexecutado: não reduz o indicador.
Ele utiliza registros verificáveis de auditoria, comparando os campos públicos
e a visibilidade dos registros relacionados na época do evento. Histórico
ausente, incompleto ou inválido é ignorado. Campos ``auto_now`` isolados não
são suficientes: podem refletir migrações ou alterações privadas. Datas do
documento também não são datas de atualização. Sem evidência, o cabeçalho
informa que a data está indisponível.

A origem, o identificador e o timestamp podem ser conferidos no Django Admin,
em Atualização do conteúdo público, somente para leitura. Não há endpoint REST
para manipular o indicador. Alterações diretas por SQL e scripts externos que
não usam o serviço não são detectadas automaticamente.
