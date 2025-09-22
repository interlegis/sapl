
3.1.164-RC5 / 2025-09-22
========================

  * Adiciona smoke test for rate limiter
  * Hot-fix: rate limiter get ip

3.1.164-RC4 / 2025-09-22
========================

  * Fix recibo proposição e adiciona rate limiter em matéria e norma

3.1.164-RC3 / 2025-09-16
========================

  * Health and Ready endpoints (#3788)
  * Fix read-only mount on k8s
  * Remove setup.py do projeto SAPL

3.1.164-RC2 / 2025-09-08
========================

  * Restaura prod settings de docker-compose
  * Restringe tipos de arquivos para upload (#3794)
  * feat: cria script para remocao de proposicoes de um autor (#3703)
  * HOT-Fix: Conserta erro introduzido no PR #3785
  * Atualização da imagem base Docker (#3787)
  * Ajustes solicitados - Relatório de Votações Nominais (#3785)
  * Refatora lógica de geração de CSV/json/xlsx (#3786)
  * Remove btn libras de media print (#3777)

3.1.164-RC1 / 2025-08-05
========================

  * Adiciona botoes de impressao na pesquisa de doc adm
  * Fix: conserta erro em historico proposicao
  * Desabilita detalhe de Justificativa Ausência para acesso público
  * Adiciona homepage do parlamentar a perfil público

3.1.164-RC0 / 2025-07-09
========================

  * Fix: nome casa duplicado
  * feat: #3771 (#3772)
  * Adiciona metadados para Google crawler
  * Remove version e monta mais um volume
  * Fix: log de aplicação
  * feat: #3769 (#3770)
  * fix: #3767 (#3768)
  * Release: 3.1.163

3.1.163 / 2025-05-21
====================

  * Fix fancycompleter incompatibility when calling shell_plus

3.1.163-RC24 / 2025-05-19
=========================

  * Implementa relatórios CSV, XLSX e JSON para Pauta de Sessão (#3744)
  * feat: adiciona pydevd-pycharm para facilitar debug usando pycharm ide (#3717)
  * Ajusta link do texto integral da Norma Jurídica nos formatos CSV, XLSX e JSON. (#3743)
  * Força mudança de senha para senhas fracas
  * Fix Chamado #643964 - Multiple definitions in dictionary at byte 0xc854c for key /Info
  * Ajusta link do texto original da Matéria nos formatos CSV, XLSX e JSON. (#3742)
  * fix: aplica um lazy loading no sortable do jquery ui pelo evento mouseenter. (#3737)
  * fix: corrige condição para mostrar btn para TAs.
  * fix: add migrate resultante do commit anterior
  * fix: torna cep opcional no model CasaLegislativa

3.1.163-RC23 / 2024-07-31
=========================

  * Otimiza recuperação de normas relacionadas (#3734)
  * hot-fix: resolve imcompatibilidade de regex com versão de produção do postgresql 9.6

3.1.163-RC21 / 2024-06-25
=========================

  * fix: descomenta código pertencente ao commit anterior
  * fix: elimina dupla extração de assinaturas eletrônicas
  * fix: remove listagem pública de OperadorAutor
  * fix: altera campo de 'resultado' ao registrar leitura em bloco
  * bump version gunicorn in setup.py
  * rebuild frontend
  * fix dependabot alerts #61 - bump version axios
  * fix: ajuste no conjunto inicial de permissões na construção de classe crud
  * Impl Mixin para gerar arquivos de pesq em diversos formatos (#3710)
  * Fix estatistica norma view (#3707)
  * bump version gunicorn, pillow
  * Build(deps): Bump pillow from 10.0.1 to 10.3.0 in /requirements (#3709)
  * fix: corrige display de data e hora de protocolor manual
  * fix: corrige carga de permissões públicas do crud
  * Add blank space when SAPN
  * fix: corrige bug na pesquisa de impressos etiquetas (#3695)
  * feat: adiciona o turno na info de materias na pauta de sessao (#3694)
  * fix: invert lógica do sapln_switch
  * fix: Update docker-compose.yaml
  * Update CHANGES.md

3.1.163-RC20 / 2023-12-04
=========================

  * HOT-FIX: Bump easy-thumbnails

3.1.163-RC19 / 2023-11-29
=========================

  * Bump Pillow

3.1.163-RC18 / 2023-11-29
=========================

  * Bump Pillow
  * Adiciona feature flag lib
  * Conserta relatoria de matérias
  * Bump Pillow version
  * feat: adiciona script para ajuste to tamanho de fontes de seçoes do painel eletronico
  * Conserta bug na paginação do Relatório de Matérias por Tramitação
  * fix: ajusta ordenacao de votos nominais por ordem alfabetica no extrato da sessao
  * fix: corrige erro de loaddata cargomesa
  * feat: adiciona check de presenca e sessao aberta na leitura em bloco da ordem do dia
  * fix: padroniza nome_parlamentar para lista de presenca e votacoes nominais no resumo da ata
  * Apaga Numeração se TipoMateriaLegislativa é apagado
  * Adiciona opção de remover formatação
  * Adiciona ordenacao em cargo mesa
  * Remove tags de considerações finais e ocorrências de sessão
  * fix: padroniza nome_parlamentar para lista de presenca e votacoes nominais no resumo da ata

3.1.163-RC17 / 2023-09-30
=========================

  * Update frontend assets
  * No resultado da pesquisa de Matéria Legislativa, ordenar pela Sequencia Regimental ou Alfabética da Sigla (#3673)
  * feat: exibe lista de parlamentares ativos por default (#3635)
  * fix: corrige espacamento no resumo da ata (#3681)
  * fix: altera nome do presidente no pdf de impressao da pauta de sessao para utilizar o nome_parlamentar (#3678)
  * feat: add link para materia e comissao na view detail da relatoria (#3682)
  * feat: adiciona link para correspondencias na pauta de sessao (#3683)
  * feat: altera exibicao de materias em tramitacao na comissao (#3684)
  * Implementa ordenação na impressão PDF da Ata Eletrônica (#3677)
  * fix: corrige render de texto rico no resumo de sessão (#3679)

3.1.163-RC16 / 2023-09-13
=========================

  * Conserta bug em relatórios com emenda longa. (#3674)
  * fix: restring acesso ao prometheus metrics para apenas ips locais/invalidos (#3668)
  * feat: adiciona filtro de autor no relatorio de tramitacao com data fim de prazo (#3671)
  * fix: verifica se existe dispositivo atualizador ao tentar montar nota alteracao (#3669)
  * Revert "Remove redirect de URLs (#3652)"

3.1.163-RC15 / 2023-08-11
=========================

  * HOT-FIX: conserta geração de CHANGES.md
  * fix: Cria novos campos para o model proposicao para salvar o usuario responsavel por cada acao (#3660)
  * Simplificação da tela de pesquisa de Matéria Legislativa (#3662)
  * bump pyyaml
  * Adiciona controle de visibilidade no módulo de relatorios
  * Adiciona coluna de justificativa de ausência (#3657)
  * Adiciona coluna de justificativa de ausência
  * Conserta lógica para embutir SAPL em iframe (#3653)
  * Move relatorios para app de relatorios (#3656)
  * Remove redirect de URLs (#3652)
  * Hot-fix: endpoint do prometheus endpoint URL
  * feat: Adiciona funcionalidade de baixar lista de documentos acessorios de um documento administrativo (#3650)

3.1.163-RC14 / 2023-06-28
=========================

  * HOT-FIX: conserta changelog
  * feat: Torna o campo Data Nascimento de Parlamentares sensivel (#3648)
  * hot-fix: desconecta signal pre_save no migrate

3.1.163-RC13 / 2023-06-18
=========================

  * Add options to abort release generation
  * Adiciona documentação automática de mudanças
  * Adiciona link para texto original em Sessão Plenária (#3644)
  * Altera nome completo para nome parlamentar em ata (#3645)
  * refactor: altera título do link e descrição de relatório
  * feat: Script to find and extract codified images pasted into text fields using the tinyMCE editor (#3643)
  * feat: adiciona a coluna assunto na list de correspondencias do expediente do dia (#3640)
  * fix: força periodo de busca no relatorio audit log (#3639)
  * add migrate de ano novo
  * impl: add campo para script do google analytics
  * refactor: corrige relatório alinhando a proposta da nomenclatura
  * hot-fix: corrige inicialização de variável
  * fix: ativa filtro que estava comentado para debug
  * impl: captura de assinaturas eletrônicas em matérias
