import './scss/voto-individual.scss'

import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { PiniaVuePlugin, createPinia } from 'pinia'

import { usePainelStore } from '../painel/store/painelStore'
import { isPermanentCloseCode, permanentCloseMessage, nextBackoffDelay, INITIAL_BACKOFF_MS, DISCONNECTED_MESSAGE } from '../painel/ws/painelSocket'
import VotoIndividual from '../../components/voto-individual/VotoIndividual.vue'
import WsStatusBanner from '../../components/painel/WsStatusBanner.vue'

Vue.component('voto-individual', VotoIndividual)
Vue.component('ws-status-banner', WsStatusBanner)

Vue.use(VueCompositionApi)
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

new Vue({
  pinia,
  el: '#voto-individual-app',
  delimiters: ['[[', ']]'],
  data () {
    return {
      sessaoId: null,
      ws: null,
      reconnectTimer: null,
      reconnectDelay: INITIAL_BACKOFF_MS,
      wsStatus: 'connecting',
      wsErrorMessage: 'Conectando ao servidor de tempo real…'
    }
  },
  mounted () {
    this.sessaoId = this.$el.dataset.sessaoId || null
    // Estado pessoal (não vem do broadcast, ver nota em fetchStatus) —
    // busca inicial aqui; daí em diante só é refeito quando o WS avisar
    // que algo mudou (sem poll periódico — ver painelSocket.js).
    this.fetchStatus()
    if (this.sessaoId) {
      this.connectWS()
    }
  },
  methods: {
    painelStore () {
      return usePainelStore()
    },
    statusURL () {
      return window.VOTO_INDIVIDUAL_STATUS_URL
    },
    wsURL () {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.sessaoId}/`
    },
    // Mesmo padrão do template legado (voto_individual.html): estado
    // pessoal (voto_parlamentar/status_message/error_message) nunca vem
    // do broadcast do painel (que é o snapshot público compartilhado por
    // todo mundo conectado) — sempre de um fetch dedicado, autenticado
    // como este Votante. O componente compara o resultado e só
    // re-renderiza quando algo muda.
    fetchStatus () {
      fetch(this.statusURL(), { credentials: 'same-origin' })
        .then(resp => resp.json())
        .then(data => {
          const comp = this.$refs.votoIndividual
          if (!comp) return
          comp.materiaId = data.materia_id ? String(data.materia_id) : ''
          comp.errorMessage = data.error_message || ''
          comp.statusMessage = data.status_message || ''
          comp.votoParlamentar = data.voto_parlamentar || ''
        })
        .catch(() => { /* tenta de novo no próximo broadcast do WS */ })
    },
    connectWS () {
      const url = this.wsURL()
      this.ws = new WebSocket(url)

      this.ws.addEventListener('open', () => {
        this.wsStatus = 'open'
        this.wsErrorMessage = ''
        this.reconnectDelay = INITIAL_BACKOFF_MS
      })

      this.ws.addEventListener('message', (message) => {
        try {
          const data = JSON.parse(message.data)
          if (data.type === 'data') {
            // Atualiza o display compartilhado da matéria (sessao/materia)
            this.painelStore().applyData(data)
            // E dispara a checagem do estado pessoal — sem poll periódico,
            // isto é a única forma de saber que algo mudou.
            this.fetchStatus()
          }
        } catch (e) {
          console.error('Voto individual WS parse error:', e)
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
    beforeDestroy () {
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
      if (this.ws) this.ws.close()
    }
  }
})
