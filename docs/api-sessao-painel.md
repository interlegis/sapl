# API: dados da Sessão Plenária para painel

```
GET /api/sessao/sessaoplenaria/{id}/painel/
```

Devolve numa única requisição tudo o que um painel eletrônico ou integração
precisa para montar uma sessão plenária. É o par de leitura do
[lote de gravação](api-sessao-lote.md): a integração baixa a sessão no início
com este endpoint, trabalha localmente e envia tudo no fim com o lote.

## Requisições por sessão

Para montar o painel pelos endpoints de listagem, uma integração precisa
buscar sessão, tipo, casa, parlamentares, mandatos, presenças, pauta,
expediente, matérias, autorias, autores, registros de votação, votos,
leituras e cadastros auxiliares, paginando de 100 em 100. Numa Casa com 21
parlamentares e 20 matérias votadas nominalmente, só os votos (420) ocupam 5
páginas.

| | Endpoints de listagem | Este endpoint |
|---|---|---|
| Montar o painel (início da sessão) | ~20, usando `expand` e filtros `__in`; bem mais sem eles | **1** |
| Sincronizar a sessão (fim) | 522 (ver [lote](api-sessao-lote.md)) | **1** com o lote |

## Permissões

Mesmas regras dos endpoints de listagem: todos os models devolvidos são de
leitura pública no SAPL, então o endpoint dispensa autenticação. Se alguma
dessas regras deixar de ser pública, o endpoint passa a exigir a permissão de
listagem de cada model e responde `403` indicando quais faltam.

A visibilidade da sessão segue a consulta pública: sessões futuras
cadastradas com antecedência (não iniciadas e sem pauta publicada) respondem
`404` para usuários não autenticados.

## Resposta

Cada bloco usa o mesmo serializer da listagem do model correspondente, então
cada registro tem exatamente o formato de `/api/<app>/<model>/`.

| Chave | Model | Conteúdo |
|---|---|---|
| `sessao_plenaria` | `SessaoPlenaria` | objeto da sessão |
| `tipo_sessao` | `TipoSessaoPlenaria` | objeto do tipo da sessão |
| `casa_legislativa` | `CasaLegislativa` | lista |
| `parlamentares` | `Parlamentar` | com mandato na legislatura da sessão ou citados nela (presença, mesa, voto, orador) |
| `mandatos` | `Mandato` | da legislatura da sessão |
| `filiacoes` | `Filiacao` | dos parlamentares acima |
| `partidos` | `Partido` | das filiações acima |
| `cargos_mesa` | `CargoMesa` | todos |
| `integrantes_mesa` | `IntegranteMesa` | mesa da sessão |
| `presencas_sessao` | `SessaoPlenariaPresenca` | da sessão |
| `presencas_ordem_dia` | `PresencaOrdemDia` | da sessão |
| `tipos_expediente` | `TipoExpediente` | todos |
| `expedientes` | `ExpedienteSessao` | da sessão |
| `expedientes_materia` | `ExpedienteMateria` | da sessão |
| `ordens_dia` | `OrdemDia` | da sessão |
| `materias` | `MateriaLegislativa` | da ordem do dia e do expediente |
| `autorias` | `Autoria` | dessas matérias |
| `autores` | `Autor` | dessas autorias |
| `tipos_autor` | `TipoAutor` | todos |
| `tipos_resultado_votacao` | `TipoResultadoVotacao` | todos |
| `registros_votacao` | `RegistroVotacao` | da ordem do dia e do expediente |
| `votos` | `VotoParlamentar` | da ordem do dia e do expediente |
| `registros_leitura` | `RegistroLeitura` | da ordem do dia e do expediente |
| `oradores` | `Orador` | explicações pessoais |
| `oradores_expediente` | `OradorExpediente` | da sessão |
| `oradores_ordem_dia` | `OradorOrdemDia` | da sessão |

Os blocos não são paginados.

## Desempenho

O número de consultas ao banco não cresce com o tamanho da sessão:
relacionamentos usados no `__str__`, campos many-to-many e `metadata` são
carregados de uma vez por bloco. Numa sessão com cerca de 600 registros, a
resposta faz menos de 100 consultas.
