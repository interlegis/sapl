// frontend/src/__apps/painel/ws/normalizePainel.js
//
// Normaliza o payload `type: "data"` recebido via WebSocket para um shape
// estável e tolerante a payload parcial. A partir da adoção do backend de
// feat/painel-websockets, o payload é o dict flat produzido por
// sapl/painel/views.py::build_dados_painel() — o mesmo usado pelo polling
// HTTP legado e pinado pelos testes sapl/painel/tests/test_broadcasts.py e
// test_consumers.py, então essa função nunca deve mudar de formato; toda
// adaptação de shape vive aqui, não em build_dados_painel().

export const DEFAULT_STATE = Object.freeze({
  sessao_aberta: false,
  painel_aberto: false,
  mostrar_voto: false,
  message: '',

  sessao: {
    sessao_plenaria: '',
    sessao_plenaria_data: '',
    sessao_plenaria_hora_inicio: '',
    sessao_solene: false,
    tema_solene: '',
    brasao: ''
  },

  cronometro_discurso: '',
  cronometro_aparte: '',
  cronometro_ordem: '',
  cronometro_consideracoes: '',

  parlamentares: [],
  oradores: [],

  materia: {},
  resultado: {
    numero_votos: {}
  },

  // Populado uma vez, a partir do contexto inicial renderizado pelo Django
  // (não vem no payload do WebSocket) — ver GAP 3 do plano de merge.
  // applyData() preserva o valor atual quando o payload não traz a lista.
  tipos_resultado: []
})

function asObject (v) {
  return v && typeof v === 'object' ? v : {}
}

function asArray (v) {
  return Array.isArray(v) ? v : []
}

function asString (v, fallback) {
  return v != null ? v : fallback
}

export function normalizePainelData (raw) {
  const d = asObject(raw)

  const parlamentares = asArray(d.presentes)
    .filter((p) => p && typeof p === 'object')
    .map((p) => ({
      id: p.id,
      parlamentar_id: p.parlamentar_id,
      nome_parlamentar: asString(p.nome, ''),
      filiacao: asString(p.partido, ''),
      fotografia: p.fotografia != null ? p.fotografia : false,
      voto: p.voto != null ? p.voto : ''
    }))

  const oradores = asArray(d.oradores)
    .filter((o) => o && typeof o === 'object')
    .map((o) => ({
      ordem_pronunciamento: o.numero,
      nome_parlamentar: asString(o.nome, '')
    }))

  console.log(d.sessao_iniciada);

  return {
    // sessao_iniciada vem de sessao.iniciada is not False (True ou None
    // contam como "iniciada" — sessões legadas ficaram com None, mesma
    // convenção de restringe_sessoes_visiveis() no backend).
    sessao_aberta: !!d.sessao_iniciada && !d.sessao_finalizada,
    painel_aberto: d.status_painel != null ? !!d.status_painel : DEFAULT_STATE.painel_aberto,    
    mostrar_voto: d.mostrar_voto != null ? !!d.mostrar_voto : DEFAULT_STATE.mostrar_voto,
    message: asString(d.msg_painel, DEFAULT_STATE.message),

    sessao: {
      sessao_plenaria: asString(d.sessao_plenaria, DEFAULT_STATE.sessao.sessao_plenaria),
      sessao_plenaria_data: asString(d.sessao_plenaria_data, DEFAULT_STATE.sessao.sessao_plenaria_data),
      sessao_plenaria_hora_inicio: asString(d.sessao_plenaria_hora_inicio, DEFAULT_STATE.sessao.sessao_plenaria_hora_inicio),
      sessao_solene: d.sessao_solene != null ? !!d.sessao_solene : DEFAULT_STATE.sessao.sessao_solene,
      tema_solene: asString(d.tema_solene, DEFAULT_STATE.sessao.tema_solene),
      brasao: asString(d.brasao, DEFAULT_STATE.sessao.brasao)
    },

    cronometro_discurso: asString(d.cronometro_discurso, DEFAULT_STATE.cronometro_discurso),
    cronometro_aparte: asString(d.cronometro_aparte, DEFAULT_STATE.cronometro_aparte),
    cronometro_ordem: asString(d.cronometro_ordem, DEFAULT_STATE.cronometro_ordem),
    cronometro_consideracoes: asString(d.cronometro_consideracoes, DEFAULT_STATE.cronometro_consideracoes),

    parlamentares,
    oradores,

    materia: {
      texto: asString(d.materia_legislativa_texto, ''),
      ementa: asString(d.materia_legislativa_ementa, ''),
      observacao: asString(d.observacao_materia, ''),
      resultado_votacao: asString(d.tipo_resultado, '')
    },

    resultado: {
      numero_votos: {
        num_presentes: d.num_presentes != null ? d.num_presentes : parlamentares.length,
        votos_sim: d.numero_votos_sim != null ? d.numero_votos_sim : 0,
        votos_nao: d.numero_votos_nao != null ? d.numero_votos_nao : 0,
        abstencoes: d.numero_abstencoes != null ? d.numero_abstencoes : 0,
        total_votos: d.total_votos != null ? d.total_votos : 0
      }
    },

    // Nunca vem no payload do WebSocket — applyData() só sobrescreve o
    // valor atual do store quando esta lista não está vazia.
    tipos_resultado: asArray(d.tipos_resultado)
  }
}
