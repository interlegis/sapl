import './scss/painel.scss'

import Vue from 'vue'
import VueCompositionApi from '@vue/composition-api'
import { PiniaVuePlugin, createPinia, mapState } from 'pinia'

import { usePainelStore } from './store/painelStore'
import { isPermanentCloseCode, permanentCloseMessage, nextBackoffDelay, INITIAL_BACKOFF_MS, DISCONNECTED_MESSAGE } from './ws/painelSocket'

import Cronometro from '../../components/painel/Cronometro.vue'
import CronometroList from '../../components/painel/CronometroList.vue'
import PainelHeader from '../../components/painel/PainelHeader.vue'
import PainelParlamentares from '../../components/painel/PainelParlamentares.vue'
import PainelOradores from '../../components/painel/PainelOradores.vue'
import PainelMateria from '../../components/painel/PainelMateria.vue'
import PainelResultado from '../../components/painel/PainelResultado.vue'
import PainelFooter from '../../components/painel/PainelFooter.vue'
import WsStatusBanner from '../../components/painel/WsStatusBanner.vue'

// register components
Vue.component('painel-cronometro', Cronometro)
Vue.component('painel-cronometro-list', CronometroList)
Vue.component('painel-header', PainelHeader)
Vue.component('painel-parlamentares', PainelParlamentares)
Vue.component('painel-oradores', PainelOradores)
Vue.component('painel-materia', PainelMateria)
Vue.component('painel-resultado', PainelResultado)
Vue.component('painel-footer', PainelFooter)
Vue.component('ws-status-banner', WsStatusBanner)

// Pinia (no Vue 2 o plugin @vue/composition-api é obrigatório)
Vue.use(VueCompositionApi)
Vue.use(PiniaVuePlugin)
const pinia = createPinia()

const PING_INTERVAL = 30000 // 30s

new Vue({
  pinia,
  el: '#painel',
  delimiters: ['[[', ']]'],
  data() {
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
    }
  },
  mounted() {
    console.log('Painel principal mounted!')
    // $el is guaranteed here
    const el = this.$el
    // prefer data-attr; fallback to global if you set it
    this.controllerId = el.dataset.controllerId || window.controllerId
    console.log(`ControllerId: ${this.controllerId}`)
    this.connectWS()

  },

  computed: {
    ...mapState(usePainelStore, ['painel_aberto', 'sessao_aberta', 'sessao', 'canRender']),
  },
  methods: {
    painelStore() {
      return usePainelStore()
    },
    wsURL() {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.controllerId}/`
    },
    updateState(data) {
       try {
          // Toda a lógica de estado (flags, sessão, parlamentares, matéria,
          // resultado e votos) vive no store Pinia. O header/footer leem a
          // sessão do store — não há mais escrita via $refs.
          this.painelStore().applyData(data)
       } catch (e) {
          console.error('Error applying painel data', e)
       }
    },
    connectWS() {
      const url = this.wsURL()
      this.ws = new WebSocket(url)

      this.ws.addEventListener('open', () => {
        this.isOpen = true;
        this.error = null
        this.wsStatus = 'open'
        this.wsErrorMessage = ''
        this.reconnectDelay = INITIAL_BACKOFF_MS

        console.log(`✅ WebSocket connected to ${url}`);

        // ping keep-alive timer (servidor responde com 'pong')
        this.pingTimer = setInterval(() => {
           const ping = JSON.stringify({ type: "ping", ts: Date.now()});
           this.ws.send(ping);
        }, PING_INTERVAL);
      })

      this.ws.addEventListener('message', (message) => {
        try {
              const data = JSON.parse(message.data)

              if (data.type === 'data') {
                    this.updateState(data);
              } else if (data.type === 'pong') {
                    console.debug('Received pong from server');
              }
        } catch (e) {
            console.error('WS parse error:', e);
        }
      })

      this.ws.addEventListener('close', (e) => {
            console.log("❌ WebSocket closed:", e);
            this.isOpen = false;
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
            this.reconnectTimer = setTimeout(() => this.connectWS(), this.reconnectDelay);
            this.reconnectDelay = nextBackoffDelay(this.reconnectDelay);
      })

      this.ws.addEventListener('error', (e) => {
            this.error = e
            console.error('❌ WebSocket error:', e)
      })
    },
    closeWS() {
        try {
            console.log(`⚠️ Closing Websocket connection: ${this.wsURL}`);
            this.ws && this.ws.close()
        } catch (_) {
            console.log("Error closing WS connection");
        }
    },
    beforeDestroy() {
        // Clear the interval before the component is destroyed
        if (this.pingTimer) {
          clearInterval(this.pingTimer);
          console.log('pingTimer Interval cleared');
        }

        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            console.log('reconnectTimer cleared');
        }

        this.closeWS();
    },
    changeFontSize(value) {
        for (var name in this.$refs){
            if (name.startsWith("sw")) {
               const cronometro = this.$refs[name]
               cronometro.changeFontSize(value)
            }
        }
    },
    startStopwatch() { if (this.isOpen) this.ws.send(JSON.stringify({ type:'notify', stopwatch:'start' })) },
  }
})
