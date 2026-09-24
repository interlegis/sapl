import './scss/votacao-simbolica.scss'
import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { PiniaVuePlugin, createPinia } from 'pinia'
import axios from 'axios'

import { usePainelStore } from '../painel/store/painelStore'
import { isPermanentCloseCode, permanentCloseMessage, nextBackoffDelay, INITIAL_BACKOFF_MS, DISCONNECTED_MESSAGE } from '../painel/ws/painelSocket'
import VotacaoSimbolica from '../../components/votacao-simbolica/VotacaoSimbolica.vue'
import WsStatusBanner from '../../components/painel/WsStatusBanner.vue'

Vue.component('votacao-simbolica', VotacaoSimbolica)
Vue.component('ws-status-banner', WsStatusBanner)

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(VueCompositionApi)
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

new Vue({ // eslint-disable-line
  pinia,
  delimiters: ['[[', ']]'],
  el: '#votacao-simbolica',
  data () {
    return {
      sessaoId: null,
      oid: null,
      mid: null,
      fase: 'ordem',
      totalPresentes: 0,
      totalVotantes: 0,
      ws: null,
      reconnectTimer: null,
      reconnectDelay: INITIAL_BACKOFF_MS,
      wsStatus: 'connecting',
      wsErrorMessage: 'Conectando ao servidor de tempo real…',
      error_message: ''
    }
  },
  mounted () {
    const el = this.$el
    this.sessaoId = el.dataset.sessaoId
    this.oid = el.dataset.oid
    this.mid = el.dataset.mid
    this.fase = el.dataset.fase || 'ordem'
    this.totalPresentes = el.dataset.totalPresentes
    this.totalVotantes = el.dataset.totalVotantes

    const tiposResultadoEl = document.getElementById('tipos-resultado')
    if (tiposResultadoEl) {
      try {
        this.painelStore().tipos_resultado = JSON.parse(tiposResultadoEl.textContent)
      } catch (e) {
        console.error('Erro ao ler tipos-resultado:', e)
      }
    }

    if (this.sessaoId) {
      this.connectWS()
    }
  },
  methods: {
    painelStore () {
      return usePainelStore()
    },
    actionUrl () {
      // Mesma URL da tela legada (VotacaoView/VotacaoExpedienteView) —
      // sessao/urls.py: continua sendo quem grava o voto (só o shell/GET
      // mudou pra v2); fase decide ordem do dia ou expediente, mesmo
      // discriminador usado pelo shell (votacao_simbolica_v2_view).
      const etapa = this.fase === 'expediente' ? 'expediente' : 'ordemdia'
      return `/sessao/${this.sessaoId}/materia/${etapa}/votacao/simbolica/${this.oid}/${this.mid}`
    },
    wsURL () {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.sessaoId}/`
    },
    connectWS () {
      this.ws = new WebSocket(this.wsURL())
      this.ws.addEventListener('open', () => {
        this.wsStatus = 'open'
        this.wsErrorMessage = ''
        this.reconnectDelay = INITIAL_BACKOFF_MS
      })
      this.ws.addEventListener('message', (message) => {
        try {
          const data = JSON.parse(message.data)
          if (data.type === 'data') {
            // applyData() espera o payload cru, não o envelope {type,
            // payload} (mesmo ajuste de painel/votacao/voto-individual
            // main.js).
            this.painelStore().applyData(data.payload)
          }
        } catch (e) {
          console.error('Votacao simbolica WS parse error:', e)
        }
      })
      this.ws.addEventListener('close', (e) => {
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
    },
    postAction (payload) {
      axios.post(this.actionUrl(), payload, {
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => {
          if (response.data.redirect_url) {
            window.location.href = response.data.redirect_url
          }
        })
        .catch(error => {
          const data = error.response && error.response.data
          this.error_message = (data && data.message) || 'Erro ao processar a votação. Tente novamente.'
        })
    },
    onCancelar () {
      this.postAction({ 'cancelar-votacao': '1' })
    },
    onSalvar (data) {
      this.postAction(data)
    },
    beforeDestroy () {
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
      if (this.ws) this.ws.close()
    }
  }
})
