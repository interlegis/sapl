import './scss/leitura-materia.scss'
import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { PiniaVuePlugin, createPinia } from 'pinia'
import axios from 'axios'

import { usePainelStore } from '../painel/store/painelStore'
import { isPermanentCloseCode, permanentCloseMessage, nextBackoffDelay, INITIAL_BACKOFF_MS, DISCONNECTED_MESSAGE } from '../painel/ws/painelSocket'
import LeituraMateria from '../../components/leitura-materia/LeituraMateria.vue'
import WsStatusBanner from '../../components/painel/WsStatusBanner.vue'

Vue.component('leitura-materia', LeituraMateria)
Vue.component('ws-status-banner', WsStatusBanner)

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(VueCompositionApi)
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

new Vue({ // eslint-disable-line
  pinia,
  delimiters: ['[[', ']]'],
  el: '#leitura-materia',
  data () {
    return {
      sessaoId: null,
      oid: null,
      mid: null,
      initialObservacao: '',
      initialMateriaTexto: '',
      initialMateriaEmenta: '',
      cancelUrl: '#',
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
    this.initialObservacao = el.dataset.observacao || ''
    this.initialMateriaTexto = el.dataset.materiaTexto || ''
    this.initialMateriaEmenta = el.dataset.materiaEmenta || ''
    // Mesma URL da tela legada (AbstractLeituraView.cancel_url) —
    // iso=1 identifica o fluxo de OrdemDia.
    this.cancelUrl = `/sessao/${this.sessaoId}/1/${this.oid}/retirar-leitura`

    if (this.sessaoId) {
      this.connectWS()
    }
  },
  methods: {
    painelStore () {
      return usePainelStore()
    },
    actionUrl () {
      return `/sessao/${this.sessaoId}/materia/ordemdia/leitura/v2/${this.oid}/${this.mid}/salvar`
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
            this.painelStore().applyData(data)
          }
        } catch (e) {
          console.error('Leitura materia WS parse error:', e)
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
    onSalvar (data) {
      axios.post(this.actionUrl(), data, {
        headers: { 'Content-Type': 'application/json' }
      })
        .then(response => {
          if (response.data.redirect_url) {
            window.location.href = response.data.redirect_url
          }
        })
        .catch(error => {
          const respData = error.response && error.response.data
          this.error_message = (respData && respData.message) || 'Erro ao registrar a leitura. Tente novamente.'
        })
    },
    onCancelar () {
      // O próprio <a :href> do componente já navega — nada a fazer aqui.
    },
    beforeDestroy () {
      if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
      if (this.ws) this.ws.close()
    }
  }
})
