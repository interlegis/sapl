# API: gravação em lote da Sessão Plenária

```
POST /api/sessao/sessaoplenaria/{id}/lote/
Authorization: Token <token>
Content-Type: application/json
```

Grava numa única requisição tudo o que uma integração (painel eletrônico,
sistema de votação etc.) precisa registrar numa sessão plenária:

| Bloco | Model | Equivale a |
|---|---|---|
| `presencas_sessao` | `SessaoPlenariaPresenca` | `POST`/`DELETE /api/sessao/sessaoplenariapresenca/` |
| `presencas_ordem_dia` | `PresencaOrdemDia` | `POST`/`DELETE /api/sessao/presencaordemdia/` |
| `votacoes` | `RegistroVotacao` + `VotoParlamentar` | `POST /api/sessao/registrovotacao/` + um `POST /api/sessao/votoparlamentar/` por voto |
| `leituras` | `RegistroLeitura` | `POST`/`PATCH`/`DELETE /api/sessao/registroleitura/` |
| `ordens_dia` | `OrdemDia` | `PATCH /api/sessao/ordemdia/{id}/` |
| `expedientes_materia` | `ExpedienteMateria` | `PATCH /api/sessao/expedientemateria/{id}/` |

## Requisições por sessão

Considerando uma Casa com 21 parlamentares, uma sessão com 20 matérias
votadas nominalmente e 10 matérias lidas no expediente:

| O que é gravado | Endpoints individuais | Lote |
|---|---|---|
| Presenças da sessão | 21 | |
| Presenças da ordem do dia | 21 | |
| Votações: 1 registro + 21 votos + 1 `PATCH` na ordem do dia, por matéria | 20 × 23 = 460 | |
| Leituras: 1 registro + 1 `PATCH` no expediente, por matéria | 10 × 2 = 20 | |
| **Total** | **522** | **1** |

De modo geral, pelos endpoints individuais são `2 × P + M × (P + 2) + 2 × L`
requisições (P parlamentares, M matérias votadas nominalmente, L matérias
lidas). Com este endpoint, a integração pode registrar a sessão localmente e
fazer **uma única requisição ao final da sessão, apenas para
sincronização** com o SAPL.

Os endpoints individuais continuam funcionando sem alteração.

## Regras

- **Qualquer combinação de blocos.** Blocos não enviados não são alterados.
  Ao menos um bloco deve ser informado.
- **Itens independentes.** Cada item é gravado em sua própria transação: a
  falha de um não impede a gravação dos demais. Uma votação (registro +
  votos) é um único item: ou é gravada inteira, ou nada é gravado.
- **Relatório por item.** A resposta traz o status de cada item, na mesma
  ordem em que foi enviado, para que apenas os que falharam sejam
  reenviados.
- **Idempotente.** Reenviar o mesmo lote não duplica presenças, registros de
  votação nem votos; os itens já gravados voltam como `inalterado`.
- **Mesmas validações e permissões.** Os dados são validados pelos mesmos
  serializers dos endpoints individuais e cada item exige as mesmas
  permissões (`sessao.add_*`, `sessao.change_*`, `sessao.delete_*`). Sem
  permissão para um bloco, os itens daquele bloco voltam com erro e os
  demais são gravados.
- **Escopo da sessão.** Matérias da ordem do dia e do expediente precisam
  pertencer à sessão da URL.
- **Ordem de processamento:** presenças da sessão, presenças da ordem do dia,
  votações, leituras, matérias da ordem do dia, matérias do expediente.
- Máximo de 500 itens por bloco.

## Payload

```json
{
  "presencas_sessao": [
    {"parlamentar": 1, "presente": true},
    {"parlamentar": 2, "presente": false}
  ],
  "presencas_ordem_dia": [
    {"parlamentar": 1}
  ],
  "votacoes": [
    {
      "ordem": 10,
      "tipo_resultado_votacao": 1,
      "observacao": "",
      "votos": [
        {"parlamentar": 1, "voto": "Sim"},
        {"parlamentar": 3, "voto": "Não"}
      ]
    },
    {
      "expediente": 4,
      "tipo_resultado_votacao": 1,
      "numero_votos_sim": 15,
      "numero_votos_nao": 2,
      "numero_abstencoes": 0
    }
  ],
  "leituras": [
    {"expediente": 5, "observacao": ""},
    {"expediente": 6, "lida": false}
  ],
  "ordens_dia": [
    {"id": 10, "resultado": "Aprovado", "votacao_aberta": false}
  ],
  "expedientes_materia": [
    {"id": 4, "resultado": "Aprovado", "votacao_aberta": false}
  ]
}
```

### Presenças

`presente` é opcional (padrão `true`):

- `true`: registra a presença se ela ainda não existir (`criado`); se já
  existir, `inalterado`.
- `false`: remove a presença se existir (`removido`); se não existir,
  `inalterado`.

Na presença da sessão, `data_sessao` é preenchida com a data de início da
sessão.

### Votações

Cada votação informa **exatamente um** entre `ordem` (id de `OrdemDia`) e
`expediente` (id de `ExpedienteMateria`). A matéria é obtida do item da
pauta.

- **Nominal**: envie `votos`. Valores aceitos: `Sim`, `Não`, `Abstenção`,
  `Não Votou`. Os totais do registro são calculados a partir dos votos; se
  `numero_votos_sim`, `numero_votos_nao` ou `numero_abstencoes` também
  forem enviados, precisam bater com o cálculo. A lista é o conjunto
  completo de votos da matéria: votos de parlamentares fora da lista são
  removidos, como acontece ao finalizar a votação nominal pela tela.
- **Simbólica / secreta**: omita `votos` e informe `numero_votos_sim`,
  `numero_votos_nao` e `numero_abstencoes`.

Se a matéria ainda não tem registro de votação, ele é criado; se já tem, é
atualizado. Usuário e IP da requisição são gravados no registro e nos votos.

A votação não altera a matéria da pauta. Para gravar `resultado`, fechar a
votação etc., use os blocos `ordens_dia`/`expedientes_materia`, que são
processados depois das votações.

### Leituras

Cada leitura informa **exatamente um** entre `ordem` e `expediente`; a
matéria é obtida do item da pauta. Há no máximo uma leitura por item da
pauta. `lida` é opcional (padrão `true`):

- `true`: cria a leitura (`criado`) ou atualiza a `observacao` da existente
  (`atualizado`/`inalterado`). Leituras duplicadas do mesmo item são
  removidas.
- `false`: remove a leitura, como "retirar leitura" na tela (`removido`); se
  não existir, `inalterado`.

Assim como a votação, a leitura não altera a matéria da pauta: para gravar
`resultado: "Matéria lida"`, use `ordens_dia`/`expedientes_materia`.

### Matérias da ordem do dia e do expediente

Cada item informa o `id` e os campos a alterar, com a mesma semântica de um
`PATCH` no endpoint individual. Não é permitido mover a matéria para outra
sessão.

## Resposta

`200 OK` sempre que o lote for processado, mesmo que algum item falhe.
Confira `resumo.erro`.

```json
{
  "sessao_plenaria": 7,
  "presencas_sessao": [
    {"parlamentar": 1, "presente": true, "status": "criado", "id": 101},
    {"parlamentar": 2, "presente": false, "status": "inalterado"}
  ],
  "presencas_ordem_dia": [
    {"parlamentar": 1, "presente": true, "status": "inalterado", "id": 55}
  ],
  "votacoes": [
    {"ordem": 10, "status": "criado", "id": 300},
    {"expediente": 4, "status": "erro",
     "erros": {"tipo_resultado_votacao": ["Este campo não pode ser nulo."]}}
  ],
  "leituras": [
    {"expediente": 5, "lida": true, "status": "criado", "id": 80},
    {"expediente": 6, "lida": false, "status": "removido"}
  ],
  "ordens_dia": [
    {"id": 10, "status": "atualizado"}
  ],
  "expedientes_materia": [
    {"id": 4, "status": "atualizado"}
  ],
  "resumo": {"criado": 3, "atualizado": 2, "removido": 1,
             "inalterado": 2, "erro": 1}
}
```

Status por item: `criado`, `atualizado`, `removido`, `inalterado`, `erro`.
Itens com `erro` trazem `erros`, no mesmo formato dos erros de validação dos
endpoints individuais.

Erros que recusam o lote inteiro:

| Código | Quando |
|---|---|
| `400` | corpo não é um objeto, bloco desconhecido, nenhum bloco, bloco que não é lista, item que não é objeto ou mais de 500 itens num bloco |
| `401`/`403` | requisição sem autenticação |
| `404` | sessão plenária inexistente |
