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
      // Estado real (não mascarado por mostrar_voto) de quem já votou —
      // nunca vem do broadcast do painel (que é a visão pública/mascarada);
      // vem de /votos-status, buscado no mount e a cada broadcast recebido.
      votosStatus: {},
    }
  },

  computed: {
    ...mapState(usePainelStore, [
      'sessao_aberta', 'painel_aberto', 'sessao',
      'parlamentares', 'materia', 'resultado', 'message', 'mostrar_voto'
    ]),
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
      this.fetchVotosStatus()
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

    voteURL () {
      return `/v2/painel/controller/${this.controllerId}/vote`
    },

    votosStatusURL () {
      return `/v2/painel/controller/${this.controllerId}/votos-status`
    },

    // Estado real (não mascarado) de quem já votou — nunca lido do store
    // (que reflete o broadcast público, mascarado quando mostrar_voto é
    // False). A Mesa precisa do valor real para não sobrescrever por
    // engano um voto que já chegou por tablet.
    fetchVotosStatus () {
      if (!this.controllerId) return
      axios.get(this.votosStatusURL())
        .then(response => {
          this.votosStatus = response.data.votos || {}
        })
        .catch(error => {
          console.error('Erro ao buscar votos-status:', error)
        })
    },

    castVote ({ parlamentar_id, voto }) {
      console.log(`Casting vote: parlamentar=${parlamentar_id}, voto=${voto}`)
      axios.post(this.voteURL(), {
        parlamentar_id: parlamentar_id,
        voto: voto
      }, {
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => {
          console.log('Vote cast successfully:', response.data)
        })
        .catch(error => {
          console.error('Error casting vote:', error.response ? error.response.data : error)
          this.error_message = 'Erro ao registrar voto. Tente novamente.'
        })
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
        this.painelStore().applyData(data)
      } catch (e) {
        console.error('Error updating state:', e)
      }
      // O broadcast é a visão pública (mascarada); o estado real de quem
      // já votou vem sempre de votos-status, refeito a cada snapshot.
      this.fetchVotosStatus()
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
