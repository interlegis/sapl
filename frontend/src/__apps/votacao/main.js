import './scss/votacao.scss'
import Vue from 'vue'
import Vuex from 'vuex'
import { mapState, mapMutations } from 'vuex'
import axios from 'axios'

// Import components
import VotacaoNominal from '../../components/votacao/VotacaoNominal.vue'
import VotacaoMateria from '../../components/votacao/VotacaoMateria.vue'
import VotacaoVotos from '../../components/votacao/VotacaoVotos.vue'
import VotacaoResultado from '../../components/votacao/VotacaoResultado.vue'
import VotacaoObservacoes from '../../components/votacao/VotacaoObservacoes.vue'

// Register components globally
Vue.component('votacao-nominal', VotacaoNominal)
Vue.component('votacao-materia', VotacaoMateria)
Vue.component('votacao-votos', VotacaoVotos)
Vue.component('votacao-resultado', VotacaoResultado)
Vue.component('votacao-observacoes', VotacaoObservacoes)

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(Vuex)

console.log('votacao main.js carregado')

// Vuex store
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
    tipos_resultado: [],
  },
  mutations: {
    sessaoStatus (state, value) {
      state.sessao_aberta = value
    },
    painelStatus (state, value) {
      state.painel_aberto = value
    },
    setParlamentares (state, parlamentares) {
      state.parlamentares = parlamentares
    },
    updateParlamentarVoto (state, { parlamentar_id, voto, voted }) {
      const p = state.parlamentares.find(p => p.parlamentar_id === parlamentar_id)
      if (p) {
        Vue.set(p, 'voto', voto)
        if (voted !== undefined) {
          Vue.set(p, 'voted', voted)
        }
      }
    },
    setOradores (state, oradores) {
      state.oradores = oradores
    },
    setMateria (state, materia) {
      state.materia = materia
    },
    setResultado (state, resultado) {
      state.resultado = resultado
    },
    setMessage (state, message) {
      state.message = message
    },
    setMostrarVoto (state, mostrar_voto) {
      state.mostrar_voto = mostrar_voto
    },
    setSessao (state, sessao) {
      state.sessao = sessao
    },
    setTiposResultado (state, tipos) {
      state.tipos_resultado = tipos
    }
  },
  getters: {
    totalVotos (state) {
      const totals = [
        { tipo: 'Sim', total: 0 },
        { tipo: 'Não', total: 0 },
        { tipo: 'Abstenção', total: 0 },
        { tipo: 'Não Votou', total: 0 }
      ]
      state.parlamentares.forEach(p => {
        if (p.voto) {
          const entry = totals.find(t => t.tipo === p.voto)
          if (entry) entry.total++
        }
      })
      return totals
    },
    numPresentes (state) {
      return state.parlamentares.length
    },
    totalVotados (state) {
      return state.parlamentares.filter(p => p.voto && p.voto !== 'Não Votou').length
    }
  }
})

const BACKOFF = 500
const PING_INTERVAL = 30000

const v = new Vue({ // eslint-disable-line
  store,
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
      error_message: '',
    }
  },

  computed: {
    ...mapState([
      'sessao_aberta', 'painel_aberto', 'sessao',
      'parlamentares', 'materia', 'resultado', 'message', 'mostrar_voto'
    ]),
  },

  mounted () {
    console.log('Votacao app mounted!')
    const el = this.$el
    this.controllerId = el.dataset.controllerId || window.controllerId
    console.log(`Votacao ControllerId: ${this.controllerId}`)
    if (this.controllerId) {
      this.connectWS()
    } else {
      this.error_message = 'Erro: controller_id não definido. Não é possível conectar ao WebSocket.'
      console.error('No controllerId found — WebSocket will not connect.')
    }
  },

  methods: {
    ...mapMutations([
      'sessaoStatus', 'painelStatus', 'setParlamentares',
      'updateParlamentarVoto', 'setOradores', 'setMateria',
      'setResultado', 'setMessage', 'setMostrarVoto', 'setSessao',
      'setTiposResultado'
    ]),

    wsURL () {
      const proto = location.protocol === 'https:' ? 'wss' : 'ws'
      return `${proto}://${location.host}/ws/painel/${this.controllerId}/`
    },

    voteURL () {
      return `/v2/painel/controller/${this.controllerId}/vote`
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
        this.sessaoStatus(data.sessao_aberta)
        this.painelStatus(data.painel_aberto)
        this.setMostrarVoto(data.mostrar_voto)

        if (data.sessao) {
          this.setSessao(data.sessao)
        }

        if (data.parlamentares) {
          data.parlamentares.forEach(p => {
            p.voto = p.voto || ''
          })
          this.setParlamentares(data.parlamentares)
        }

        if (data.message) {
          this.setMessage(data.message)
        }

        if (data.oradores) {
          this.setOradores(data.oradores)
        }

        if (data.materia) {
          this.setMateria(data.materia)

          if (data.materia.resultado) {
            this.setResultado(data.materia.resultado)

            // If there are existing votes, apply them to parlamentares
            if (data.materia.resultado.votos_parlamentares) {
              const votos = data.materia.resultado.votos_parlamentares
              if (Array.isArray(votos)) {
                // Array format: [{parlamentar_id: X, voto: "Sim"}, ...]
                votos.forEach(v => {
                  if (v && v.parlamentar_id && v.voto) {
                    this.updateParlamentarVoto({
                      parlamentar_id: v.parlamentar_id,
                      voto: v.voto
                    })
                  }
                })
              } else if (typeof votos === 'object') {
                // Object format from DB view: {"5": {"voto": "Sim", "parlamentar_id": 5, ...}, ...}
                Object.keys(votos).forEach(key => {
                  const v = votos[key]
                  if (v && v.voto) {
                    this.updateParlamentarVoto({
                      parlamentar_id: parseInt(key),
                      voto: v.voto
                    })
                  }
                })
              }
            }
          } else {
            this.setResultado({})
          }
        } else {
          this.setMateria({})
          this.setResultado({})
        }

        if (data.tipos_resultado) {
          this.setTiposResultado(data.tipos_resultado)
        }
      } catch (e) {
        console.error('Error updating state:', e)
      }
    },

    handleVoteUpdate (data) {
      console.log('Received vote update via WebSocket:', data)
      this.updateParlamentarVoto({
        parlamentar_id: data.parlamentar_id,
        voto: data.voto
      })
    },

    connectWS () {
      const url = this.wsURL()
      this.ws = new WebSocket(url)

      this.ws.addEventListener('open', () => {
        this.isOpen = true
        this.error = null
        this.error_message = ''
        console.log(`✅ Votação WebSocket connected to ${url}`)
        this.ws.send(JSON.stringify({ type: 'echo', message: 'Votacao client connected' }))

        this.pingTimer = setInterval(() => {
          this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }))
        }, PING_INTERVAL)
      })

      this.ws.addEventListener('message', (message) => {
        try {
          const data = JSON.parse(message.data)
          console.debug('Votacao WS message:', data)

          if (data.type === 'data') {
            this.updateState(data)
          } else if (data.type === 'vote.update') {
            this.handleVoteUpdate(data)
          } else if (data.type === 'echo') {
            console.log('Votacao echo:', data)
          } else if (data.type === 'ping') {
            // ignore pings
          }
        } catch (e) {
          console.error('Votacao WS parse error:', e)
        }
      })

      this.ws.addEventListener('close', (e) => {
        console.log('❌ Votação WebSocket closed:', e)
        this.isOpen = false
        this.reconnectTimer = setTimeout(() => this.connectWS(), BACKOFF)
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
