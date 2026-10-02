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

  cronometro_discurso: null,
  cronometro_aparte: null,
  cronometro_ordem: null,
  cronometro_consideracoes: null,
  cronometro_ativo: 'discurso',

  // Só significa algo enquanto há matéria nominal aberta pra registro —
  // ver PainelConsumer (type: "registro_toggle") / VotacaoNominal.vue.
  registro_aberto: false,

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

/**
 * Normaliza o valor do cronômetro recebido do backend.
 *
 * O backend novo envia um dict:
 *   { action, duration, start_ts?, remaining_at_stop? }
 *
 * O backend antigo (cache legado) pode enviar uma string ('start'|'stop'|'reset').
 * O valor null/undefined significa "sem estado" (nunca foi configurado).
 *
 * Retorna sempre um objeto normalizado ou null.
 */
function normalizeCronometro (v) {
  if (v == null) return null
  // Formato legado: string simples
  if (typeof v === 'string') {
    return {
      action: v,
      duration: 300,
      start_ts: null,
      remaining_at_start: 300,
      remaining_at_stop: null,
      updated_at: null
    }
  }
  if (typeof v === 'object') {
    const duration = v.duration != null ? v.duration : 300
    const remaining_at_start = v.remaining_at_start != null ? v.remaining_at_start : duration
    const remaining_at_stop = v.remaining_at_stop != null ? v.remaining_at_stop : null
    return {
      action: v.action || '',
      duration,
      start_ts: v.start_ts != null ? v.start_ts : null,
      remaining_at_start,
      remaining_at_stop,
      updated_at: v.updated_at != null ? v.updated_at : null
    }
  }
  return null
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
      voto: p.voto != null ? p.voto : '',
      // Só true quando o próprio parlamentar votou (voto individual/
      // tablet) — nunca quando o voto veio do operador pelo mesmo
      // <select> que lê isto, mesmo que o valor pareça igual.
      voto_por_tablet: !!p.voto_por_tablet
    }))

  const oradores = asArray(d.oradores)
    .filter((o) => o && typeof o === 'object')
    .map((o) => ({
      ordem_pronunciamento: o.numero,
      nome_parlamentar: asString(o.nome, '')
    }))

  console.log(d.sessao_iniciada)

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

    // Cronômetros: agora objetos {action, duration, start_ts?, remaining_at_stop?}
    // ou null quando nunca configurados. O store repassa para CronometroList.vue
    // que aplica a ação e configura o tempo inicial de cada Cronometro.vue.
    cronometro_discurso: normalizeCronometro(d.cronometro_discurso),
    cronometro_aparte: normalizeCronometro(d.cronometro_aparte),
    cronometro_ordem: normalizeCronometro(d.cronometro_ordem),
    cronometro_consideracoes: normalizeCronometro(d.cronometro_consideracoes),
    cronometro_ativo: asString(d.cronometro_ativo, DEFAULT_STATE.cronometro_ativo),

    registro_aberto: d.registro_aberto != null ? !!d.registro_aberto : DEFAULT_STATE.registro_aberto,

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
