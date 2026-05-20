# Matriz de Impacto - Soft Delete

Branch analisada: `codex/login-govbr`

Esta matriz classifica as tabelas do SAPL para a mudança de hard delete para exclusao logica.

## Decisoes Aprovadas

- Campos padrao nas tabelas SAPL em escopo:
  - `excluido`
  - `excluido_em`
  - `excluido_por`
  - `motivo_exclusao`
- Auditoria central:
  - `base_auditoriaexclusaologica`
  - `dados_registro`
  - `motivo_restauracao`
- Todo soft delete exige `motivo_exclusao`.
- Toda restauracao exige `motivo_restauracao`.
- Restauracao sera permitida apenas ao grupo `Administrador do Sistema`.
- O grupo `Administrador do Sistema` deve ter todas as permissoes.
- Usuarios comuns poderao visualizar registros que eles mesmos excluiram apenas pelo futuro fluxo "Meus excluidos".
- Usuarios Gov.br poderao reativar o proprio usuario quando a conta estiver desativada por exclusao logica.
- Retencao permanente: nao ha purge/hard delete operacional previsto.
- Tabelas Django/terceiros devem usar `is_active` quando aplicavel; tabelas tecnicas permanecem sem soft delete.
- A exclusao de `base_appconfig`, `base_casalegislativa` e `painel_*` sera bloqueada.
- Para relacoes M2M automaticas, a auditoria central do servico de exclusao e suficiente.
- A tabela `parlamentares_mandato` permanece no escopo dos trabalhos.
- Nenhum endpoint atual devera mostrar registros excluidos pelo proprio usuario; inclusive `Proposicao` so exibira excluidos no futuro fluxo "Meus excluidos".

## Legenda

| Classificacao | Significado |
| --- | --- |
| Soft delete | Adicionar campos `excluido*`, ocultar nas consultas comuns, auditar exclusao e restauracao. |
| is_active | Usar flag propria de ativacao/desativacao, com auditoria central. |
| Manter tecnico | Manter sem soft delete; tabela tecnica, cache, migracao, sessao, token, permissao, view ou tabela com exclusao bloqueada. |

## Fluxos Transversais Impactados

| Fluxo | Impacto |
| --- | --- |
| CRUD generico | `CrudDeleteView` deve trocar delete fisico por soft delete com motivo obrigatorio. |
| APIs DRF | Querysets devem ocultar `excluido=True`, exceto endpoints administrativos. |
| Auditoria | `base_auditlog` hoje registra `D` via `post_delete`; soft delete deve registrar `D` manualmente. |
| Solr/Haystack | Indices devem remover/ocultar objetos excluidos logicamente e reindexar em restauracao. |
| Arquivos anexos | Overrides de `delete()` que removem arquivos fisicos devem ser ajustados para preservar arquivos no soft delete. |
| Permissoes | Criar grupo `Administrador do Sistema` e permissoes de ver/restaurar excluidos. |
| Gov.br | `auth_user.is_active=False` por exclusao logica deve permitir reativacao via login Gov.br. |
| Unicidade | Chaves unicas de tabelas com soft delete devem virar indices unicos parciais para registros nao excluidos. |
| Views SQL | Views devem filtrar tabelas base com `excluido=False`. |

## Fluxos Por Modulo

| Modulo | Fluxos impactados |
| --- | --- |
| `audiencia` | Cadastro de audiencias, anexos, arquivos de pauta/ata/anexo, consultas publicas. |
| `base` | Autores, operadores de autor, tipo de autor, auditoria, usuarios, configuracoes. |
| `comissoes` | Comissoes, composicoes, participacoes, reunioes, pautas, documentos acessorios. |
| `compilacao` | Texto articulado, dispositivos, publicacoes, notas, vides, owners e regras de ordenacao. |
| `lexml` | Provedor/publicador LexML e configuracoes de integracao. |
| `materia` | Materias, proposicoes, tramitacoes, autoria, anexadas, documentos, relatorias, numeracao, view de materia em tramitacao. |
| `norma` | Normas juridicas, autoria, anexos, legislacao citada, relacoes, estatisticas e view de estatisticas. |
| `painel` | Estado operacional de painel e cronometro. |
| `parlamentares` | Parlamentares, mandatos, filiacao, dependentes, mesa, frente, bloco, votantes. |
| `protocoloadm` | Protocolos, documentos administrativos, tramitacoes, anexados, vinculos e acompanhamentos. |
| `sessao` | Sessoes plenarias, expediente, ordem do dia, presencas, votacoes, justificativas, leituras, correspondencias. |
| Django/terceiros | Usuarios, grupos, permissoes, sessoes, tokens, thumbnails, feature flags. |

## Matriz Tabela Por Tabela

### Audiencia

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `audiencia_anexoaudienciapublica` | Soft delete | Anexos de audiencia; preservar arquivo fisico e auditar restauracao. |
| `audiencia_audienciapublica` | Soft delete | Cadastro principal de audiencia; possui arquivos removidos hoje no `delete()`. |
| `audiencia_tipoaudienciapublica` | Soft delete | Tabela auxiliar mantida por usuario. |

### Auth, Tokens e Django

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `auth_group` | Manter tecnico | Grupos e permissoes; criar `Administrador do Sistema`; nao usar soft delete. |
| `auth_group_permissions` | Manter tecnico | Relacao tecnica de permissoes. |
| `auth_permission` | Manter tecnico | Permissoes geradas por Django/SAPL. |
| `auth_user` | is_active | Usar `is_active=False` com auditoria central; permitir reativacao Gov.br quando desativado por exclusao logica. |
| `auth_user_groups` | Manter tecnico | Relacao tecnica de grupos de usuario. |
| `auth_user_user_permissions` | Manter tecnico | Relacao tecnica de permissoes diretas. |
| `authtoken_token` | Manter tecnico | Token operacional; hard delete em rotacao deve continuar. |
| `django_admin_log` | Manter tecnico | Log tecnico/administrativo imutavel. |
| `django_content_type` | Manter tecnico | Metadados do Django. |
| `django_migrations` | Manter tecnico | Controle de migrations. |
| `django_session` | Manter tecnico | Sessao temporaria. |

### Base

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `base_appconfig` | Manter tecnico | Exclusao bloqueada; configuracao singleton/global. |
| `base_auditlog` | Manter tecnico | Auditoria existente; deve receber evento `D` manual em soft delete. |
| `base_autor` | Soft delete | Autor e vinculos genericos; afeta Materia, Norma, Protocolo, Parlamentares, Comissoes. |
| `base_casalegislativa` | Manter tecnico | Exclusao bloqueada; configuracao institucional. |
| `base_metadata` | Manter tecnico | Metadados tecnicos/signaturas; preservar junto ao objeto. |
| `base_operadorautor` | Soft delete | Associacao usuario/autor; hoje pode ser removida ao editar usuario. |
| `base_tipoautor` | Soft delete | Tabela auxiliar; parte e gerada pelo sistema, mas administravel. |

### Comissoes

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `comissoes_cargocomissao` | Soft delete | Tabela auxiliar. |
| `comissoes_comissao` | Soft delete | Cadastro principal; campo `ativa` e de dominio, nao substitui `excluido`. |
| `comissoes_composicao` | Soft delete | Periodos/composicoes; impacta participacoes. |
| `comissoes_documentoacessorio` | Soft delete | Documento de reuniao; preservar arquivo fisico. |
| `comissoes_participacao` | Soft delete | Integrantes/cargos em composicao. |
| `comissoes_periodo` | Soft delete | Tabela auxiliar de periodo. |
| `comissoes_reuniao` | Soft delete | Reunioes, pauta e anexos; possui arquivos removidos hoje no `delete()`. |
| `comissoes_tipocomissao` | Soft delete | Tabela auxiliar. |

### Compilacao

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `compilacao_dispositivo` | Soft delete | Estrutura de texto articulado; muitos deletes reposicionam arvore/ordem. |
| `compilacao_nota` | Soft delete | Notas de dispositivos. |
| `compilacao_perfilestruturaltextoarticulado` | Soft delete | Configuracao estrutural administravel. |
| `compilacao_publicacao` | Soft delete | Publicacoes de texto articulado. |
| `compilacao_textoarticulado` | Soft delete | Documento principal do texto articulado. |
| `compilacao_textoarticulado_owners` | Soft delete | Relacao de proprietarios; auditoria central do servico de exclusao basta para esta relacao M2M. |
| `compilacao_tipodispositivo` | Soft delete | Tabela auxiliar estrutural. |
| `compilacao_tipodispositivorelationship` | Soft delete | Relacoes pai/filho permitidas; hoje valida unicidade. |
| `compilacao_tiponota` | Soft delete | Tabela auxiliar. |
| `compilacao_tipopublicacao` | Soft delete | Tabela auxiliar. |
| `compilacao_tipotextoarticulado` | Soft delete | Tabela auxiliar vinculada a content type. |
| `compilacao_tipotextoarticulado_perfis` | Soft delete | M2M auxiliar; auditoria central do servico de exclusao basta. |
| `compilacao_tipovide` | Soft delete | Tabela auxiliar. |
| `compilacao_veiculopublicacao` | Soft delete | Tabela auxiliar. |
| `compilacao_vide` | Soft delete | Referencias/vide entre dispositivos. |

### Easy Thumbnails

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `easy_thumbnails_source` | Manter tecnico | Cache/derivacao de imagem. |
| `easy_thumbnails_thumbnail` | Manter tecnico | Cache/derivacao de imagem. |
| `easy_thumbnails_thumbnaildimensions` | Manter tecnico | Cache/derivacao de imagem. |

### LexML

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `lexml_lexmlprovedor` | Soft delete | Configuracao de provedor LexML. |
| `lexml_lexmlpublicador` | Soft delete | Configuracao de publicador LexML. |

### Materia

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `materia_acompanhamentomateria` | Soft delete | Acompanhamento por email/usuario. |
| `materia_anexada` | Soft delete | Relacao entre materias; impacta listagens de anexadas. |
| `materia_assuntomateria` | Soft delete | Tabela auxiliar. |
| `materia_autoria` | Soft delete | Autoria de materia; unicidade autor/materia deve considerar nao excluidos. |
| `materia_configetiquetamaterialegislativa` | Soft delete | Configuracao administravel de etiquetas. |
| `materia_despachoinicial` | Soft delete | Despachos/comissoes iniciais. |
| `materia_documentoacessorio` | Soft delete | Documento acessorio; preservar arquivo fisico e Solr. |
| `materia_historicoproposicao` | Soft delete | Historico de proposicao; em regra nao deve ser apagado fisicamente. |
| `materia_materiaassunto` | Soft delete | Relacao materia/assunto. |
| `materia_materialegislativa` | Soft delete | Cadastro principal; unicidade tipo/numero/ano deve virar indice parcial. |
| `materia_materiaemtramitacao` | Manter tecnico | View SQL; deve filtrar `materia_materialegislativa` e `materia_tramitacao` nao excluidas. |
| `materia_numeracao` | Soft delete | Numeracao complementar por tipo/ano. |
| `materia_orgao` | Soft delete | Tabela auxiliar/unidade. |
| `materia_origem` | Soft delete | Tabela auxiliar. |
| `materia_parecer` | Soft delete | Parecer de relatoria/materia. |
| `materia_pautareuniao` | Soft delete | Relacao materia/reuniao de comissao. |
| `materia_proposicao` | Soft delete | Proposicao; regras atuais bloqueiam exclusao apos envio/recebimento. |
| `materia_regimetramitacao` | Soft delete | Tabela auxiliar. |
| `materia_relatoria` | Soft delete | Relatoria de materia. |
| `materia_statustramitacao` | Soft delete | Tabela auxiliar; exclusao impacta tramitacoes. |
| `materia_tipodocumento` | Soft delete | Tabela auxiliar. |
| `materia_tipofimrelatoria` | Soft delete | Tabela auxiliar. |
| `materia_tipomaterialegislativa` | Soft delete | Tabela auxiliar; impacta numeracao e materias. |
| `materia_tipoproposicao` | Soft delete | Tabela auxiliar vinculada a content type. |
| `materia_tipoproposicao_perfis` | Soft delete | M2M auxiliar; auditoria central do servico de exclusao basta. |
| `materia_tramitacao` | Soft delete | Tramitação; deletes atuais recalculam `em_tramitacao`; restauracao deve recalcular tambem. |
| `materia_unidadetramitacao` | Soft delete | Unidade de tramitacao; impacta Materia, Protocolo, Sessao. |

### Norma

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `norma_anexonormajuridica` | Soft delete | Anexos de norma; preservar arquivo fisico. |
| `norma_assuntonorma` | Soft delete | Tabela auxiliar. |
| `norma_autorianorma` | Soft delete | Autoria de norma; unicidade autor/norma deve considerar nao excluidos. |
| `norma_legislacaocitada` | Soft delete | Relacao materia/norma citada. |
| `norma_normaestatisticas` | Manter tecnico | Estatisticas de acesso; nao representa exclusao de dado de usuario. |
| `norma_normajuridica` | Soft delete | Cadastro principal; preservar texto integral e Solr. |
| `norma_normajuridica_assuntos` | Soft delete | M2M de assuntos; auditoria central do servico de exclusao basta. |
| `norma_normarelacionada` | Soft delete | Relacao entre normas. |
| `norma_tiponormajuridica` | Soft delete | Tabela auxiliar. |
| `norma_tipovinculonormajuridica` | Soft delete | Tabela auxiliar. |
| `norma_viewnormasestatisticas` | Manter tecnico | View SQL; deve ocultar normas excluidas. |

### Painel

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `painel_cronometro` | Manter tecnico | Exclusao bloqueada; estado operacional/temporario do painel. |
| `painel_painel` | Manter tecnico | Exclusao bloqueada; estado operacional do painel. |

### Parlamentares

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `parlamentares_bloco` | Soft delete | Cadastro de bloco; possui autores vinculados. |
| `parlamentares_bloco_partidos` | Soft delete | M2M bloco/partido; auditoria central do servico de exclusao basta. |
| `parlamentares_blococargo` | Soft delete | Cargo em bloco. |
| `parlamentares_blocomembro` | Soft delete | Membros de bloco. |
| `parlamentares_cargomesa` | Soft delete | Tabela auxiliar. |
| `parlamentares_coligacao` | Soft delete | Coligacao eleitoral. |
| `parlamentares_composicaocoligacao` | Soft delete | Relacao coligacao/partido. |
| `parlamentares_composicaomesa` | Soft delete | Composicao de mesa diretora. |
| `parlamentares_dependente` | Soft delete | Dependentes; preservar historico. |
| `parlamentares_filiacao` | Soft delete | Filiacoes partidarias. |
| `parlamentares_frente` | Soft delete | Frente parlamentar; possui autores vinculados. |
| `parlamentares_frentecargo` | Soft delete | Cargo em frente. |
| `parlamentares_frenteparlamentar` | Soft delete | Membros/cargos de frente. |
| `parlamentares_legislatura` | Soft delete | Legislatura; tabela estrutural de alto impacto. |
| `parlamentares_mandato` | Soft delete | Mandatos; historico parlamentar. |
| `parlamentares_mesadiretora` | Soft delete | Mesa diretora. |
| `parlamentares_nivelinstrucao` | Soft delete | Tabela auxiliar. |
| `parlamentares_parlamentar` | Soft delete | Cadastro principal; campo `ativo` e de dominio, nao substitui `excluido`. Preservar fotografia. |
| `parlamentares_partido` | Soft delete | Partidos; preservar logotipo. |
| `parlamentares_sessaolegislativa` | Soft delete | Sessao legislativa. |
| `parlamentares_situacaomilitar` | Soft delete | Tabela auxiliar. |
| `parlamentares_tipoafastamento` | Soft delete | Tabela auxiliar. |
| `parlamentares_tipodependente` | Soft delete | Tabela auxiliar. |
| `parlamentares_votante` | Soft delete | Vinculo parlamentar/usuario votante; hoje pode ser removido ao editar usuario. |

### Protocolo Administrativo

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `protocoloadm_acompanhamentodocumento` | Soft delete | Acompanhamento por email/usuario. |
| `protocoloadm_anexado` | Soft delete | Relacao de documentos anexados. |
| `protocoloadm_documentoacessorioadministrativo` | Soft delete | Documento acessorio; preservar arquivo fisico. |
| `protocoloadm_documentoadministrativo` | Soft delete | Cadastro principal; preservar texto integral e respeitar restricao. |
| `protocoloadm_protocolo` | Soft delete | Protocolo; `anulado` e regra de negocio, nao substitui `excluido`. Unicidade numero/ano deve virar parcial. |
| `protocoloadm_statustramitacaoadministrativo` | Soft delete | Tabela auxiliar. |
| `protocoloadm_tipodocumentoadministrativo` | Soft delete | Tabela auxiliar. |
| `protocoloadm_tramitacaoadministrativo` | Soft delete | Tramitacao; deletes atuais recalculam status; restauracao deve recalcular tambem. |
| `protocoloadm_vinculodocadminmateria` | Soft delete | Vinculo documento/materia; unicidade deve considerar nao excluidos. |

### Sessao

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `sessao_bancada` | Soft delete | Bancadas por legislatura/partido. |
| `sessao_cargobancada` | Soft delete | Cargo de bancada. |
| `sessao_consideracoesfinais` | Soft delete | Consideracoes finais da sessao. |
| `sessao_correspondencia` | Soft delete | Correspondencias vinculadas a documento administrativo. |
| `sessao_expedientemateria` | Soft delete | Materias do expediente; impacta leitura/votacao/retirada. |
| `sessao_expedientesessao` | Soft delete | Expediente textual; possui delete customizado. |
| `sessao_integrantemesa` | Soft delete | Integrantes da mesa da sessao. |
| `sessao_justificativaausencia` | Soft delete | Justificativas; preservar anexo. |
| `sessao_justificativaausencia_materias_da_ordem_do_dia` | Soft delete | M2M justificativa/ordem; auditoria central do servico de exclusao basta. |
| `sessao_justificativaausencia_materias_do_expediente` | Soft delete | M2M justificativa/expediente; auditoria central do servico de exclusao basta. |
| `sessao_ocorrenciasessao` | Soft delete | Ocorrencias da sessao. |
| `sessao_orador` | Soft delete | Oradores. |
| `sessao_oradorexpediente` | Soft delete | Oradores do expediente. |
| `sessao_oradorordemdia` | Soft delete | Oradores da ordem do dia. |
| `sessao_ordemdia` | Soft delete | Ordem do dia; impacta votacao/leitura/retirada. |
| `sessao_presencaordemdia` | Soft delete | Presencas da ordem do dia. |
| `sessao_registroleitura` | Soft delete | Registro de leitura. |
| `sessao_registrovotacao` | Soft delete | Registro de votacao; varios deletes operacionais hoje recriam votacao. |
| `sessao_resumoordenacao` | Soft delete | Configuracao/ordenacao de resumo da sessao. |
| `sessao_retiradapauta` | Soft delete | Retiradas de pauta. |
| `sessao_sessaoplenaria` | Soft delete | Cadastro principal; preservar pauta, ata e anexos. |
| `sessao_sessaoplenariapresenca` | Soft delete | Lista de presenca da sessao. |
| `sessao_tipoexpediente` | Soft delete | Tabela auxiliar. |
| `sessao_tipojustificativa` | Soft delete | Tabela auxiliar. |
| `sessao_tiporesultadovotacao` | Soft delete | Tabela auxiliar. |
| `sessao_tiporetiradapauta` | Soft delete | Tabela auxiliar. |
| `sessao_tiposessaoplenaria` | Soft delete | Tabela auxiliar. |
| `sessao_votoparlamentar` | Soft delete | Voto parlamentar; preservar trilha de auditoria. |

### Waffle

| Tabela | Classificacao | Fluxos/observacoes |
| --- | --- | --- |
| `waffle_flag` | Manter tecnico | Feature flag de terceiro. |
| `waffle_flag_groups` | Manter tecnico | Relacao tecnica de feature flag. |
| `waffle_flag_users` | Manter tecnico | Relacao tecnica de feature flag. |
| `waffle_sample` | Manter tecnico | Feature flag de terceiro. |
| `waffle_switch` | Manter tecnico | Feature flag de terceiro. |

## Pontos De Alto Risco

| Ponto | Risco | Acao antes de implementar |
| --- | --- | --- |
| Views SQL | Podem mostrar excluidos se nao forem reescritas. | Alterar views e criar testes de regressao. |
| M2M automaticas | Django nao tem model explicito para campos `excluido*`. | Auditar pelo servico central de exclusao; nao converter para `through` explicito nesta etapa. |
| Unicidade | Registros excluidos bloqueiam novo cadastro com mesma chave. | Converter constraints para indices parciais no PostgreSQL. |
| Arquivos | Overrides de `delete()` apagam arquivos fisicos. | Separar `soft_delete()` de `hard_delete_permanente()`; hard delete nao usado em operacao normal. |
| Gov.br | `auth_user.is_active=False` pode significar bloqueio ou exclusao logica. | Auditoria deve distinguir motivo e permitir reativacao apenas de exclusao logica. |
| Votacoes e tramitacoes | Deletes atuais recalculam estado operacional. | Soft delete/restauracao devem recalcular estado derivado. |
| Solr | Resultado de busca pode exibir excluidos. | Ajustar index querysets e executar reindexacao apos migracao. |

## Endpoints Publicos e APIs Para Confirmacao

Regra sugerida para confirmacao:

- Consultas anonimas/publicas: nao devem expor registros com `excluido=True`.
- Usuarios autenticados comuns: podem ver registros que eles mesmos excluiram apenas no futuro fluxo "Meus excluidos".
- `Administrador do Sistema`: pode ver e restaurar todos os excluidos por telas/endpoints administrativos especificos.
- APIs devem aplicar a mesma regra das telas: list/detail publicos filtram excluidos; rotas administrativas ou "meus excluidos" usam permissao explicita.

### Paginas Publicas Web

| Modulo | Endpoints publicos candidatos | Dados impactados | Confirmacao sugerida |
| --- | --- | --- | --- |
| Base | `/`, `/sistema/pesquisa-textual`, `/sistema/estatisticas`, `/login/govbr/`, `/auth/govbr/callback/`, `/email/validate/...`, `/recuperar-senha/...` | Home, busca textual, estatisticas, login, validacao/recuperacao de conta. | Home/busca/estatisticas nao devem expor excluidos. Gov.br deve permitir reativacao apenas do proprio usuario excluido logicamente. |
| Audiencia | `/audiencia/`, detalhes de audiencia e anexos gerados por `AudienciaCrud` e `AnexoAudienciaPublicaCrud`. | `audiencia_audienciapublica`, `audiencia_anexoaudienciapublica`. | Publico nao ve excluidos. |
| Comissoes | `/comissao/`, `/comissao/<pk>`, composicoes, participacoes, reunioes, documentos acessorios e `/comissao/<pk>/materias-em-tramitacao`. | Comissao, composicao, participacao, reuniao, documentos e materias em tramitacao. | Publico nao ve excluidos; se uma reuniao/composicao for excluida, ocultar tambem filhos na consulta publica. |
| Materia | `/materia/pesquisar-materia`, `/materia/<pk>`, `/materia/<pk>/ta`, autoria, anexadas, despachos, assuntos, numeracao, legislacao citada, tramitacao, relatoria e documentos acessorios. | Materias e relacoes publicas do processo legislativo. | Publico nao ve excluidos. Confirmar se autores/operadores autenticados poderao ver seus proprios excluidos em uma tela separada. |
| Materia - acompanhamento | `/materia/<pk>/acompanhar-materia/`, `/materia/<pk>/acompanhar-confirmar`, `/materia/<pk>/acompanhar-excluir`. | `materia_acompanhamentomateria`. | Nao expor acompanhamentos excluidos; cancelar acompanhamento deve usar soft delete com auditoria. |
| Materia - arquivos | `/materia/docacessorio/zip/<pk>`, `/materia/docacessorio/pdf/<pk>`. | Arquivos de documentos acessorios. | Publico nao deve baixar arquivos de registros excluidos. |
| Norma | `/norma/pesquisar`, `/norma/<pk>`, `/norma/<pk>/ta`, anexos e autoria de norma. | Normas juridicas, anexos, autoria e texto articulado. | Publico nao ve excluidos; se norma for excluida, ocultar anexos/autorias/publicacoes associadas. |
| Parlamentares | `/parlamentar/`, `/parlamentar/<pk>`, `/parlamentar/<pk>/materias`, `/parlamentar/<pk>/normas`, `/parlamentar/<pk>/frentes/`, filiacao, dependentes, participacoes, relatorias, proposicoes e `MandatoCrud`. | Parlamentares e historico politico, incluindo `parlamentares_mandato`. | Publico nao ve excluidos. `parlamentares_mandato` permanece no escopo. |
| Mesa diretora | `/mesa-diretora/`, `/mesa-diretora/altera-field-mesa-public-view/`. | Mesa diretora e composicao. | Publico nao ve excluidos. Rotas de alteracao continuam protegidas quando modificarem dados. |
| Protocolo administrativo | `/docadm/pesq-doc-adm`, `/docadm/<pk>`, `/docadm/texto_integral/<pk>`, anexados, tramitacoes, documentos acessorios e vinculos, quando documentos administrativos estiverem ostensivos. | Documentos administrativos e anexos. | Publico nao ve excluidos; respeitar `restrito=True` e configuracao ostensivo/restritivo. |
| Protocolo - acompanhamento | `/docadm/<pk>/acompanhar-documento/`, `/docadm/<pk>/acompanhar-confirmar`, `/docadm/<pk>/acompanhar-excluir`. | `protocoloadm_acompanhamentodocumento`. | Nao expor acompanhamentos excluidos; cancelar acompanhamento deve usar soft delete com auditoria. |
| Sessao plenaria | `/sessao/pesquisar-sessao`, `/sessao/<pk>`, `/sessao/<pk>/resumo`, `/sessao/<pk>/resumo_ata`, `/sessao/<pk>/expediente`, `/sessao/<pk>/presenca`, `/sessao/<pk>/presencaordemdia`, `/sessao/<pk>/mesa`, `/sessao/<pk>/ocorrencia_sessao`, `/sessao/<pk>/consideracoes_finais`. | Sessao, presencas, mesa, expediente, ocorrencias e consideracoes finais. | Publico nao ve excluidos; resumos devem filtrar filhos excluidos. |
| Pauta e votacoes | `/sessao/pauta-sessao`, `/sessao/pauta-sessao/pesquisar-pauta`, `/sessao/pauta-sessao/<pk>/pdf`, `/sessao/<pk>/votacao-nominal-transparencia/...`, `/sessao/<pk>/votacao-simbolica-transparencia/...`. | Pauta, ordem do dia, expediente, registros de votacao e votos. | Publico nao ve excluidos; se votacao for excluida logicamente, nao aparecer em transparencia publica. |
| Painel | `/painel-principal/<pk>`, `/painel/<pk>/dados`, `/painel/mensagem`, `/painel/parlamentar`, `/painel/votacao`, `/painel/verifica-painel`, `/painel/cronometro`. | Estado operacional de painel/cronometro. | Exclusao bloqueada para `painel_*`; endpoints nao precisam expor excluidos. |
| Compilacao/texto articulado | `/ta/`, `/ta/<pk>`, `/ta/<ta_id>/text`, `/ta/<ta_id>/text/vigencia/...`, `/ta/<ta_id>/publicacao`, `/ta/<ta_id>/publicacao/<pk>`. | Texto articulado, dispositivos, publicacoes, notas e vides. | Publico so ve conteudo com permissao de visualizacao; nao expor excluidos. |
| LexML | `/sistema/lexml/provedor/`, `/sistema/lexml/request_search/...`, `/sistema/lexml/oai`. | Integracao LexML. | Confirmar se provedor/publicador seguem como tecnico; consultas LexML nao devem expor excluidos SAPL. |
| Relatorios publicos/operacionais | `/relatorios/materia`, `/relatorios/ordem-dia`, `/relatorios/<pk>/sessao-plenaria`, `/relatorios/<pk>/resumo_ata`, `/relatorios/<pk>/sessao-plenaria-pdf`, `/relatorios/<pk>/materia-tramitacao`, demais relatorios em `/sistema/relatorios/...`. | Relatorios de materia, norma, sessao, audiencia, reuniao, documentos e votacoes. | Aplicar a mesma regra do fluxo de origem; relatorios publicos nao exibem excluidos. |

### APIs Publicas ou Semi-Publicas

| API | Endpoints candidatos | Dados impactados | Confirmacao sugerida |
| --- | --- | --- | --- |
| API schema/docs | `/api/schema/`, `/api/schema/swagger-ui/`, `/api/schema/redoc/`. | Documentacao OpenAPI. | Sem dados de negocio; nao se aplica. |
| Auth/token | `/api/auth/token`, `/api/recriar-token/<pk>`. | Token de autenticacao. | Nao expor excluidos; recriar token segue admin. |
| Health/version | `/version/`, `/health/`, `/ready/`. | Estado tecnico. | Sem dados de negocio; nao se aplica. |
| API Audiencia | `/api/audiencia/tipoaudienciapublica/`, `/api/audiencia/audienciapublica/`, `/api/audiencia/anexoaudienciapublica/`. | Audiencias e anexos. | GET publico nao ve excluidos. |
| API Base | `/api/base/casalegislativa/`, `/api/base/tipoautor/`, `/api/base/autor/`, `/api/base/autor/possiveis/`, `/api/base/autor/provaveis/`, `/api/base/autor/<tipo_generico>/`, `/api/contenttypes/contenttype/`. | Casa legislativa, autores, tipos e contenttypes. | `base_casalegislativa` tem exclusao bloqueada; autores excluidos nao aparecem publicamente. |
| API Comissoes | `/api/comissoes/cargocomissao/`, `/api/comissoes/tipocomissao/`, `/api/comissoes/periodo/`, `/api/comissoes/comissao/`, `/api/comissoes/composicao/`, `/api/comissoes/participacao/`, `/api/comissoes/reuniao/`, `/api/comissoes/documentoacessorio/`, `/api/comissoes/comissao/<pk>/materiaemtramitacao/`. | Comissoes, composicoes, participacoes, reunioes, documentos e materias em tramitacao. | GET publico nao ve excluidos. |
| API Compilacao | `/api/compilacao/tipotextoarticulado/`, `/api/compilacao/tiponota/`, `/api/compilacao/tipovide/`, `/api/compilacao/tipopublicacao/`, `/api/compilacao/veiculopublicacao/`, `/api/compilacao/tipodispositivo/`, `/api/compilacao/dispositivo/`, `/api/compilacao/publicacao/`, `/api/compilacao/vide/`, `/api/compilacao/nota/`. | Tipos, dispositivos, publicacoes, vides e notas. | GET publico nao ve excluidos; texto privado continua protegido por regra de permissao. |
| API Materia | `/api/materia/materialegislativa/`, `/api/materia/anexada/`, `/api/materia/autoria/`, `/api/materia/despachoinicial/`, `/api/materia/documentoacessorio/`, `/api/materia/materiaassunto/`, `/api/materia/assuntomateria/`, `/api/materia/numeracao/`, `/api/materia/tramitacao/`, `/api/materia/materiaemtramitacao/`, `/api/materia/relatoria/`, `/api/materia/pautareuniao/`, auxiliares de materia. | Materias e relacoes publicas. | GET publico nao ve excluidos. |
| API Proposicao | `/api/materia/proposicao/`, `/api/materia/proposicao/<pk>/`. | Proposicoes. | GET publico por permissao customizada, mas queryset diferencia anonimo, dono e operador. O endpoint atual nao deve expor excluidos; proposicoes excluidas pelo dono aparecerao somente em "Meus excluidos". |
| API Norma | `/api/norma/normajuridica/`, `/api/norma/normarelacionada/`, `/api/norma/anexonormajuridica/`, `/api/norma/autorianorma/`, `/api/norma/legislacaocitada/`, `/api/norma/assuntonorma/`, `/api/norma/tiponormajuridica/`, `/api/norma/tipovinculonormajuridica/`, `/api/norma/normaestatisticas/`. | Normas, relacoes, anexos, autoria e estatisticas. | GET publico nao ve excluidos. |
| API Parlamentares | `/api/parlamentares/parlamentar/`, `/api/parlamentares/parlamentar/<pk>/proposicoes/`, `/api/parlamentares/parlamentar/search_parlamentares/`, `/api/parlamentares/legislatura/<pk>/parlamentares/`, `/api/parlamentares/mandato/`, filiacao, dependente, mesa, frente, bloco, votante e auxiliares. | Parlamentares e historico, incluindo `parlamentares_mandato`. | GET publico nao ve excluidos. Nenhum endpoint adicional autorizado a mostrar excluidos do proprio usuario. |
| API Protocolo administrativo | `/api/protocoloadm/documentoadministrativo/`, `/api/protocoloadm/documentoacessorioadministrativo/`, `/api/protocoloadm/tramitacaoadministrativo/`, `/api/protocoloadm/anexado/`. | Documentos administrativos e relacoes. | GET pode ser publico quando documentos administrativos estiverem ostensivos; sempre ocultar excluidos e respeitar `restrito=True`. |
| API Sessao | `/api/sessao/sessaoplenaria/`, `/api/sessao/sessaoplenaria/years/`, `/api/sessao/sessaoplenaria/<pk>/expedientes/`, `/api/sessao/sessaoplenaria/<pk>/ecidadania/`, `/api/sessao/sessaoplenaria/ecidadania/`, `/api/sessao-plenaria/`, `/api/sessao-plenaria/<pk>/`. | Sessao plenaria, e-Cidadania e expediente. | GET publico nao ve excluidos; endpoint legado deve receber o mesmo filtro. |
| API Sessao - itens | `/api/sessao/expedientemateria/`, `/api/sessao/ordemdia/`, `/api/sessao/registrovotacao/`, `/api/sessao/votoparlamentar/`, `/api/sessao/retiradapauta/`, `/api/sessao/registroleitura/`, `/api/sessao/presencaordemdia/`, `/api/sessao/sessaoplenariapresenca/`, `/api/sessao/correspondencia/`, demais auxiliares. | Itens da sessao, votacoes, presencas e correspondencias. | GET publico nao ve excluidos; correspondencias respeitam restricao do documento administrativo. |
| API Painel | `/api/painel/painel/`, `/api/painel/cronometro/`. | Estado operacional do painel. | Exclusao bloqueada para `painel_*`; nao expor excluidos. |

### Endpoints Novos Necessarios

| Endpoint/fluxo | Objetivo | Quem acessa |
| --- | --- | --- |
| Tela/API de excluidos por modulo | Listar registros `excluido=True` para auditoria e restauracao. | `Administrador do Sistema`. |
| Acao de restauracao | Restaurar registro com `motivo_restauracao` obrigatorio. | `Administrador do Sistema`. |
| "Meus excluidos" | Permitir ao usuario comum visualizar registros que ele mesmo excluiu. | Usuario autenticado, limitado por `excluido_por`. |
| Reativacao Gov.br | Reativar `auth_user.is_active=False` quando a auditoria indicar exclusao logica do proprio usuario. | Proprio usuario Gov.br. |

## Informacoes Ainda Necessarias

- Definir o desenho funcional e a URL do futuro fluxo "Meus excluidos".
