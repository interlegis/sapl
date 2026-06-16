import './scss/painel.scss'

// main.js (Vue 2)
import Vue from 'vue'
import Vuex from 'vuex'
import { mapState } from 'vuex';
import { mapMutations } from 'vuex'

import Cronometro from '../../components/painel/Cronometro.vue'
import CronometroList from '../../components/painel/CronometroList.vue'
import PainelHeader from '../../components/painel/PainelHeader.vue'
import PainelParlamentares from '../../components/painel/PainelParlamentares.vue'
import PainelOradores from '../../components/painel/PainelOradores.vue'
import PainelMateria from '../../components/painel/PainelMateria.vue'
import PainelResultado from '../../components/painel/PainelResultado.vue'
import PainelFooter from '../../components/painel/PainelFooter.vue'
import alarm from '../../assets/audio/ring.mp3'

// register components
Vue.component('painel-cronometro', Cronometro)
Vue.component('painel-cronometro-list', CronometroList)
Vue.component('painel-header', PainelHeader)
Vue.component('painel-parlamentares', PainelParlamentares)
Vue.component('painel-oradores', PainelOradores)
Vue.component('painel-materia', PainelMateria)
Vue.component('painel-resultado', PainelResultado)
Vue.component('painel-footer', PainelFooter)

// global store
Vue.use(Vuex)
const store = new Vuex.Store({
  state: {
    sessao_aberta: false,
    painel_aberto: false,
    mostrar_voto: false,
    sessao: {},
    parlamentares: [],
    oradores: [],
    materia: {},
    resultado: {},
    message: '',
  },
  mutations: {
    sessaoStatus(state, value) {
        state.sessao_aberta = value;
    },
    painelStatus(state, value) {
        state.painel_aberto = value;
    },
    setParlamentares(state, parlamentares) {
        state.parlamentares = parlamentares;
    },
    updateParlamentares(state, votos_parlamentares) {
        if (votos_parlamentares) {
            let votosMap = votos_parlamentares;
            if (Array.isArray(votos_parlamentares)) {
                votosMap = {};
                votos_parlamentares.forEach((item) => {
                    if (item) {
                        Object.keys(item).forEach((key) => {
                            votosMap[key] = item[key];
                        });
                    }
                });
            }
            state.parlamentares = state.parlamentares.map((p) => {
                if (p.parlamentar_id in votosMap) {
                    return { ...p, voto: votosMap[p.parlamentar_id].voto };
                }
                return p;
            });
        }
    },
    setOradores(state, oradores) {
        state.oradores = oradores;
    },
    setMateria(state, materia) {
        state.materia = materia;
    },
    setResultado(state, resultado) {
        state.resultado = resultado;
    },
    setMessage(state, message) {
        state.message = message;
    },
    setMostrarVoto(state, mostrar_voto) {
        state.mostrar_voto = mostrar_voto;
    },
    setSessao(state, sessao) {
        state.sessao = sessao;
    }
  },
  actions: {},
  getters: {}
})

const BACKOFF = 500
const PING_INTERVAL = 30000 // 30s

new Vue({
  store,
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
    ...mapState(["painel_aberto", "sessao_aberta", "sessao"]),
    canRender () {
        return this.sessao_aberta && this.painel_aberto;
    },
  },
  methods: {
    ...mapMutations(['sessaoStatus', 'painelStatus','setParlamentares',
                     'updateParlamentares', 'setOradores', 'setMateria',
                     'setResultado', 'setMessage', 'setMostrarVoto', 'setSessao']),
    wsURL() {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.controllerId}/`
    },
    handleStopWatchEvent(data) {
        console.log("Received a stopwatch update event");
        //TODO: check if action is valid
        //TODO: check if stopwatch ID is valid

        const stopwatch = this.$refs[data.id]
        //TODO: stopwatch has to buzz at 00:30 AND 00:00
        if (data.action == "start" || data.action == "stop") {
            console.log(`Stopwatch Event: ${data}`)
            stopwatch.handleStartStop();
        } else if (data.action == "reset") {
            stopwatch.handleReset();
        } else if (data.action == "set") {
            //TODO: check if time is passed and valid
            stopwatch.initialTime = stopwatch.time
            stopwatch.time = stopwatch.time
        } else {
            console.log(`Invalid stopwatch action ${data.action}`);
            return
        }

        // TODO: check if WebSocket is open and handle submission errors
        // TODO: save stopwatch state on localStorage?
        // Return updated stopwatch status
        //   "stopwatch": {
        //        "type": "stopwatch.state",
        //        "id": "sw:main",
        //        "status": "running",
        //        "started_at_ms": 1699990000123,
        //        "elapsed_ms": 5320
        //    }
        // TODO: change started_at and elapsed to milliseconds
        this.ws.send(JSON.stringify({type:'stopwatch.state',
                                     id: stopwatch.id,
                                     status: stopwatch.isRunning ? "running" : "stopped",
                                     started_at_s: stopwatch.initialTime,
                                     elapsed_s: stopwatch.initialTime - stopwatch.time,
                                    }))

    },
    updateState(data) {
       try {
          // CONFIG GERAIS
          this.sessaoStatus(data.sessao_aberta);
          this.painelStatus(data.painel_aberto);
          this.setMostrarVoto(data.mostrar_voto);

          if (data.sessao) {
             this.setSessao(data.sessao);
          }

          // PARLAMENTARES
          if (data.parlamentares) {
             // pre-popula para Vuex capturar mudanca de estado de 'voto'
             data.parlamentares.forEach(p => p.voto = '');
             this.setParlamentares(data.parlamentares);
          }

          // HEADER DO PAINEL
          const headerInstance = this.$refs.painelHeader;
          headerInstance.sessao_plenaria = data.sessao.sessao_plenaria

          // FOOTER DO PAINEL (brasão + relógio)
          const footerInstance = this.$refs.painelFooter;
          if (footerInstance) {
            footerInstance.brasao = data.sessao.brasao;
          }

          if (data.message) {
            this.setMessage(data.message);
          }

          // ORADORES
          if (data.oradores) {
            this.setOradores(data.oradores);
          }

          // MATERIA
          if (data.materia) {
            this.setMateria(data.materia);

            // RESULTADO
            if (data.materia.resultado) {
              this.setResultado(data.materia.resultado);

              if (data.materia.resultado.votos_parlamentares) {
                this.updateParlamentares(data.materia.resultado.votos_parlamentares);
              }
            } else {
              this.setResultado({});
            }
          } else {
            this.setMateria({});
            this.setResultado({});
          }
        } catch (e) {
            console.error('Error', e);
        }
    },
    connectWS() {
      const url = this.wsURL()
      this.ws = new WebSocket(url)

      this.ws.addEventListener('open', () => {
        this.isOpen = true;
        this.error = null

        console.log(`✅ WebSocket connected to ${url}`);

        // send an initial message to the server
        this.ws.send(JSON.stringify({ type: "echo", message: "Client connected" }));

        // ping keep-alive timer
        this.pingTimer = setInterval(() => {
           const ping = JSON.stringify({ type: "ping", ts: Date.now()});
           console.log(`Sending ping ${ping}`)
           // TODO: check if this.ws object is still usable!!!
           this.ws.send(ping);
        }, PING_INTERVAL);
      })

      this.ws.addEventListener('message', (message) => {
        try {
              const data = JSON.parse(message.data)
              console.debug(`${JSON.stringify(data)}`)

              if (data.type === 'data') {
                    this.updateState(data);
              } else if (data.type == 'echo') {
                    console.log(`Received ack from server: ${JSON.stringify(data)}`);
              } else if (data.type == 'ping') {
                    console.log(`Received ping from server: ${JSON.stringify(data)}`);
              } else if (data.type == 'stopwatch.update') {
                    this.handleStopWatchEvent(data);
              }
        } catch (e) {
            console.error('WS parse error:', e);
        }
      })

      this.ws.addEventListener('close', (e) => {
            console.log("❌ WebSocket closed:", e);
            this.isOpen = false;
            this.reconnectTimer = setTimeout(() => this.connectWS(), BACKOFF);
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
