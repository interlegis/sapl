import './scss/votacao.scss'
import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { PiniaVuePlugin, createPinia, mapState } from 'pinia'
import axios from 'axios'

// Store Pinia compartilhado com o app painel
import { usePainelStore } from '../painel/store/painelStore'
import { isPermanentCloseCode, permanentCloseMessage, nextBackoffDelay, INITIAL_BACKOFF_MS, DISCONNECTED_MESSAGE } from '../painel/ws/painelSocket'

// Import components
import VotacaoNominal from '../../components/votacao/VotacaoNominal.vue'
import VotacaoMateria from '../../components/votacao/VotacaoMateria.vue'
import VotacaoVotos from '../../components/votacao/VotacaoVotos.vue'
import VotacaoResultado from '../../components/votacao/VotacaoResultado.vue'
import VotacaoObservacoes from '../../components/votacao/VotacaoObservacoes.vue'
import WsStatusBanner from '../../components/painel/WsStatusBanner.vue'

// Register components globally
Vue.component('votacao-nominal', VotacaoNominal)
Vue.component('votacao-materia', VotacaoMateria)
Vue.component('votacao-votos', VotacaoVotos)
Vue.component('votacao-resultado', VotacaoResultado)
Vue.component('votacao-observacoes', VotacaoObservacoes)
Vue.component('ws-status-banner', WsStatusBanner)

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

// Pinia (no Vue 2 o plugin @vue/composition-api é obrigatório)
Vue.use(VueCompositionApi)
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

console.log('votacao main.js carregado')

const PING_INTERVAL = 30000

const v = new Vue({ // eslint-disable-line
  pinia,
  delimiters: ['[[', ']]'],
  el: '#votacao',
  data () {
    return {
      controllerId: null,
      ws: null,
      isOpen: false,
      error: null,
      pingTimer: null,
      reconnectTimer: null,
      reconnectDelay: INITIAL_BACKOFF_MS,
      wsStatus: 'connecting',
      wsErrorMessage: 'Conectando ao servidor de tempo real…',
      error_message: '',
    }
  },

  computed: {
    ...mapState(usePainelStore, [
      'sessao_aberta', 'painel_aberto', 'sessao',
      'parlamentares', 'materia', 'resultado', 'message', 'mostrar_voto',
      'registro_aberto'
    ]),
    // Estado real (não mascarado) de quem já votou — a conexão WS desta
    // tela é reconhecida como operador/Mesa pelo backend
    // (PainelConsumer.is_operator), então parlamentares[].voto já vem sem
    // máscara aqui, ao contrário da conexão do telão público. Substitui o
    // fetch a /votos-status (removido — ver PainelConsumer.painel_refresh).
    votosStatus () {
      const map = {}
      this.parlamentares.forEach((p) => {
        if (p.voto) map[p.parlamentar_id] = p.voto
      })
      return map
    },
    // Quais linhas devem ficar travadas pro operador — só quando o voto
    // veio do próprio parlamentar (tablet), nunca quando veio do próprio
    // operador (por este <select> ou pelo formulário legado em lote):
    // votosStatus sozinho não distingue isso, ver voto_por_tablet.
    votosTravados () {
      const map = {}
      this.parlamentares.forEach((p) => {
        if (p.voto_por_tablet) map[p.parlamentar_id] = true
      })
      return map
    },
  },

  mounted () {
    console.log('Votacao app mounted!')
    const el = this.$el
    this.controllerId = el.dataset.controllerId || window.controllerId
    console.log(`Votacao ControllerId: ${this.controllerId}`)
    // tipos_resultado nunca vem do broadcast do painel — populado uma vez
    // a partir do contexto inicial renderizado pelo Django (ver GAP 3 do
    // plano de merge). applyData() preserva esse valor depois (só
    // sobrescreve quando o payload realmente traz uma lista não vazia).
    const tiposResultadoEl = document.getElementById('tipos-resultado')
    if (tiposResultadoEl) {
      try {
        this.painelStore().tipos_resultado = JSON.parse(tiposResultadoEl.textContent)
      } catch (e) {
        console.error('Erro ao ler tipos-resultado:', e)
      }
    }
    if (this.controllerId) {
      this.connectWS()
    } else {
      this.error_message = 'Erro: controller_id não definido. Não é possível conectar ao WebSocket.'
      console.error('No controllerId found — WebSocket will not connect.')
    }
  },

  methods: {
    painelStore () {
      return usePainelStore()
    },

    wsURL () {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.controllerId}/`
    },

    // Voto vai pelo WebSocket já aberto (PainelConsumer.receive_json,
    // type: "vote") em vez de um POST HTTP separado — o consumer grava e
    // já dispara o refresh pro grupo (ver vote_ack/vote_error no
    // listener de mensagens). vote_controller (HTTP) continua existindo
    // por compatibilidade, mas esta tela não o chama mais.
    castVote ({ parlamentar_id, voto }) {
      console.log(`Casting vote: parlamentar=${parlamentar_id}, voto=${voto}`)
      if (!this.isOpen) {
        this.error_message = 'Sem conexão em tempo real. Aguarde reconectar e tente de novo.'
        return
      }
      this.ws.send(JSON.stringify({ type: 'vote', parlamentar_id, voto }))
    },

    // Bloqueia/reabre o registro de novos votos — equivalente ao
    // bloquear-registro-votacao/reabrir-votacao de nominal.html (tela
    // legada), agora pelo WS. aberto=true BLOQUEIA (nome do campo
    // registro_aberto é herdado do modelo, mesma semântica de sempre).
    toggleRegistro (aberto) {
      if (!this.isOpen) {
        this.error_message = 'Sem conexão em tempo real. Aguarde reconectar e tente de novo.'
        return
      }
      this.ws.send(JSON.stringify({ type: 'registro_toggle', aberto }))
    },

    cancelURL () {
      return `/v2/painel/controller/${this.controllerId}/cancel`
    },

    closeURL () {
      return `/v2/painel/controller/${this.controllerId}/close`
    },

    onCancelar () {
      console.log('Votação cancelada')
      axios.post(this.cancelURL(), {}, {
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => {
          console.log('Votação cancelada com sucesso:', response.data)
          if (response.data.redirect_url) {
            window.location.href = response.data.redirect_url
          }
        })
        .catch(error => {
          console.error('Erro ao cancelar votação:', error.response ? error.response.data : error)
          const msg = error.response && error.response.data && error.response.data.message
            ? error.response.data.message
            : 'Erro ao cancelar votação. Tente novamente.'
          this.error_message = msg
        })
    },

    onFechar (data) {
      console.log('Fechar votação:', data)
      if (!data.resultado_selected) {
        this.error_message = 'Não é possível finalizar a votação sem nenhum resultado da votação.'
        return
      }
      axios.post(this.closeURL(), {
        resultado_id: data.resultado_selected,
        observacoes: data.observacoes || ''
      }, {
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => {
          console.log('Votação finalizada com sucesso:', response.data)
          this.error_message = ''
          if (response.data.redirect_url) {
            window.location.href = response.data.redirect_url
          }
        })
        .catch(error => {
          console.error('Erro ao fechar votação:', error.response ? error.response.data : error)
          const msg = error.response && error.response.data && error.response.data.message
            ? error.response.data.message
            : 'Erro ao fechar votação. Tente novamente.'
          this.error_message = msg
        })
    },

    updateState (data) {
      try {
        // Toda a normalização/aplicação de estado vive no store Pinia.
        // applyData() espera o payload cru (normalizePainelData() lê
        // d.sessao_iniciada etc. diretamente) — não o envelope {type,
        // payload} inteiro da mensagem WS, senão sessao_aberta/
        // painel_aberto nunca saem de DEFAULT_STATE e a tela não renderiza
        // nada. Mesmo ajuste já feito em painel/main.js e voto-individual/
        // main.js.
        this.painelStore().applyData(data.payload)
      } catch (e) {
        console.error('Error updating state:', e)
      }
    },

    connectWS () {
      const url = this.wsURL()
      this.ws = new WebSocket(url)

      this.ws.addEventListener('open', () => {
        this.isOpen = true
        this.error = null
        this.error_message = ''
        this.wsStatus = 'open'
        this.wsErrorMessage = ''
        this.reconnectDelay = INITIAL_BACKOFF_MS
        console.log(`✅ Votação WebSocket connected to ${url}`)

        this.pingTimer = setInterval(() => {
          this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }))
        }, PING_INTERVAL)
      })

      this.ws.addEventListener('message', (message) => {
        try {
          const data = JSON.parse(message.data)

          if (data.type === 'data') {
            this.updateState(data)
          } else if (data.type === 'pong') {
            console.debug('Votacao: pong recebido')
          } else if (data.type === 'vote_ack') {
            console.log('Voto confirmado pelo servidor:', data)
            this.error_message = ''
          } else if (data.type === 'vote_error') {
            console.error('Erro ao registrar voto:', data.message)
            this.error_message = data.message || 'Erro ao registrar voto. Tente novamente.'
          } else if (data.type === 'registro_toggle_ack') {
            console.log('Registro bloqueado/reaberto:', data)
            this.error_message = ''
          } else if (data.type === 'registro_toggle_error') {
            console.error('Erro ao bloquear/reabrir registro:', data.message)
            this.error_message = data.message || 'Erro ao bloquear/reabrir registro. Tente novamente.'
          }
        } catch (e) {
          console.error('Votacao WS parse error:', e)
        }
      })

      this.ws.addEventListener('close', (e) => {
        console.log('❌ Votação WebSocket closed:', e)
        this.isOpen = false
        if (this.pingTimer) {
          clearInterval(this.pingTimer)
          this.pingTimer = null
        }
        if (isPermanentCloseCode(e.code)) {
          this.wsStatus = 'error'
          this.wsErrorMessage = permanentCloseMessage(e.code)
          return
        }
        this.wsStatus = 'reconnecting'
        this.wsErrorMessage = DISCONNECTED_MESSAGE
        this.reconnectTimer = setTimeout(() => this.connectWS(), this.reconnectDelay)
        this.reconnectDelay = nextBackoffDelay(this.reconnectDelay)
      })

      this.ws.addEventListener('error', (e) => {
        this.error = e
        console.error('❌ Votação WebSocket error:', e)
      })
    },

    closeWS () {
      try {
        this.ws && this.ws.close()
      } catch (_) {
        console.log('Error closing WS')
      }
    },

    beforeDestroy () {
      if (this.pingTimer) {
        clearInterval(this.pingTimer)
      }
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
      }
      this.closeWS()
    }
  }
})
