// Reconexão do WebSocket do painel (/ws/painel/<sessao_id>/), compartilhada
// pelos cinco apps Vue que se conectam nele (painel, votacao, voto-individual,
// votacao-simbolica, leitura-materia). Não há mais fallback de polling HTTP —
// isto é a única fonte de atualização, então quem usa isto precisa também
// expor o status ao usuário (ver WsStatusBanner.vue), não só logar no console.

const MIN_BACKOFF_MS = 1000
const MAX_BACKOFF_MS = 30000

// Códigos fechados explicitamente por PainelConsumer.connect()
// (sapl/painel/consumers.py) para condições que uma nova tentativa não
// resolve sozinha — não faz sentido continuar reconectando com backoff.
const PERMANENT_CLOSE_MESSAGES = {
  4401: 'Sessão expirada ou usuário não autenticado. Faça login novamente e recarregue a página.',
  4403: 'Seu usuário não tem permissão para acessar esta tela.',
  4404: 'Sessão plenária não encontrada.'
}

export function isPermanentCloseCode (code) {
  return Object.prototype.hasOwnProperty.call(PERMANENT_CLOSE_MESSAGES, code)
}

export function permanentCloseMessage (code) {
  return PERMANENT_CLOSE_MESSAGES[code]
}

export const INITIAL_BACKOFF_MS = MIN_BACKOFF_MS

// Redis fora do ar (com o Daphne no ar) tende a fechar a conexão logo após
// aceitá-la, não a recusar a abertura — então o "erro de conexão" real é
// "fechou de novo pouco depois de eu tentar", não só "nunca abriu".
export function nextBackoffDelay (currentDelayMs) {
  const base = Math.min(currentDelayMs * 2, MAX_BACKOFF_MS)
  // +/-30% de jitter — evita que várias telas conectadas na mesma sessão
  // reconectem todas no mesmo instante depois de uma queda do Daphne,
  // o que bateria em build_dados_painel() ao mesmo tempo para todas.
  return Math.round(base * (0.7 + Math.random() * 0.6))
}

export const DISCONNECTED_MESSAGE =
  'Conexão em tempo real perdida. Tentando reconectar…'
