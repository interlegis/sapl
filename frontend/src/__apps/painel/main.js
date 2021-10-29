import './scss/painel.scss'
import Vue from 'vue'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

//  Variaveis dos cronometros
var time_d = null
var time_o = null
var time_a = null
var time_c = null
var time_p = null
var timeEnd_o = null
var timeEnd_d = null
var timeEnd_a = null
var timeEnd_c = null
var timeEnd_p = null
var audioAlertFinish = document.getElementById('audio')
var cronometroStart = []
var started = []
const socket = new WebSocket(`ws://${window.location.host}/ws/painel/`)

const v = new Vue({ // eslint-disable-line
  delimiters: ['[[', ']]'],
  el: '#app-painel',
  data () {
    return {
      message: null, // TODO: remove when porting to VueJS is done
      polling: null,
      painel_aberto: true,
      sessao_plenaria: '',
      sessao_plenaria_data: '',
      sessao_plenaria_hora_inicio: '',
      brasao: '',
      cronometro_discurso: '',
      cronometro_aparte: '',
      cronometro_ordem: '',
      cronometro_consideracoes: '',
      cronometro_personalizado: '',
      sessao_solene: false,
      sessao_solene_tema: '',
      presentes: [],
      oradores: [],
      numero_votos_sim: 0,
      numero_votos_nao: 0,
      numero_abstencoes: 0,
      num_presentes: 0,
      total_votos: 0,
      sessao_finalizada: true,
      materia_legislativa_texto: '',
      materia_legislativa_ementa: '',
      observacao_materia: '',
      mat_em_votacao: 'Matéria em Votação',
      resultado_votacao_css: '',
      tipo_resultado: '',
      tipo_votacao: '',
      teste: null,
      running: [],
      status_cronometro_discurso: '',
      status_cronometro_aparte: '',
      status_cronometro_ordem: '',
      status_cronometro_consideracoes: '',
      status_cronometro_personalizado: '',
      relogio: '',
      fontSize: 20
    }
  },
  methods: {
    msgMateria () {
      if (this.tipo_resultado && this.painel_aberto) {
        if (this.tipo_votacao !== 'Leitura' && (!this.sessao_finalizada || this.sessao_finalizada !== undefined) && !this.sessao_solene) {
          this.resultado_votacao_css = 'color: #45919D'
          this.mat_em_votacao = 'Matéria em Votação'
        } else {
          this.resultado_votacao_css = 'color: #45919D'
          this.mat_em_votacao = 'Matéria em Leitura'
        }

        this.resultado_votacao = this.tipo_resultado

        var resultado_votacao_upper = this.resultado_votacao.toUpperCase()

        if (resultado_votacao_upper.search('APROV') !== -1) {
          this.resultado_votacao_css = 'color: #7CFC00'
          this.mat_em_votacao = 'Matéria Votada'
        } else if (resultado_votacao_upper.search('REJEIT') !== -1) {
          this.resultado_votacao_css = 'color: red'
          this.mat_em_votacao = 'Matéria Votada'
        } else if (resultado_votacao_upper.search('LIDA') !== -1) {
          this.mat_em_votacao = 'Matéria Lida'
        }
      } else {
        this.resultado_votacao = ''
        if (this.tipo_votacao !== 'Leitura') {
          this.mat_em_votacao = 'Matéria em Votação'
        } else {
          this.mat_em_votacao = 'Matéria em Leitura'
        }
      }
    },
    atribuiColor (parlamentar) {
      var color = 'white'
      if (parlamentar.voto === 'Voto Informado' || parlamentar.voto === '') {
        color = 'yellow'
      } else {
        if (parlamentar.voto === 'Sim') {
          color = 'green'
        } else if (parlamentar.voto === 'Não') {
          color = 'red'
        }
      }
      parlamentar.color = color
    },
    capObservacao (texto) {
      if (texto && texto.length > 151) {
        return texto.substr(0, 145).concat('(...)')
      }
      return texto
    },
    fetchData () {
      // TODO: how to get no hardcoded URL?
      const objeto = JSON.parse(this.teste)
      this.brasao = objeto.brasao
      this.painel_aberto = objeto.status_painel
      this.sessao_finalizada = objeto.sessao_finalizada
      this.sessao_plenaria = objeto.sessao_plenaria
      this.sessao_plenaria_data = 'Data Início: ' + objeto.sessao_plenaria_data
      this.sessao_plenaria_hora_inicio = 'Hora Início: ' + objeto.sessao_plenaria_hora_inicio
      this.sessao_solene = objeto.sessao_solene
      this.sessao_solene_tema = objeto.sessao_solene_tema
      this.status_cronometro_discurso = objeto.status_cronometro_discurso
      this.status_cronometro_ordem = objeto.status_cronometro_ordem
      this.status_cronometro_aparte = objeto.status_cronometro_aparte
      this.status_cronometro_consideracoes = objeto.status_cronometro_consideracoes
      this.status_cronometro_personalizado = objeto.status_cronometro_personalizado
      setInterval(() => {
        this.atualizaRelogio()
      }, 50)

      this.presentes = objeto.presentes
      this.presentes.forEach(parlamentar => {
        this.atribuiColor(parlamentar)
      })

      this.oradores = objeto.oradores

      this.materia_legislativa_texto = objeto.materia_legislativa_texto
      this.numero_votos_sim = objeto.numero_votos_sim
      this.numero_votos_nao = objeto.numero_votos_nao
      this.numero_abstencoes = objeto.numero_abstencoes
      this.num_presentes = objeto.num_presentes
      this.total_votos = objeto.total_votos

      this.materia_legislativa_texto = objeto.materia_legislativa_texto
      this.materia_legislativa_ementa = objeto.materia_legislativa_ementa
      this.observacao_materia = this.capObservacao(objeto.observacao_materia)

      this.tipo_resultado = objeto.tipo_resultado
      this.tipo_votacao = objeto.tipo_votacao
      this.msgMateria()

      // Cronometros
      cronometroStart[0] = objeto.cronometro_discurso
      cronometroStart[1] = objeto.cronometro_aparte
      cronometroStart[2] = objeto.cronometro_ordem
      cronometroStart[3] = objeto.cronometro_consideracoes
      cronometroStart[4] = objeto.cronometro_personalizado

      this.running[0] = 0
      this.running[1] = 0
      this.running[2] = 0
      this.running[3] = 0
      this.running[4] = 0

      // Status cronometro
      if (this.status_cronometro_discurso === 'S') {
        this.stop(1)
      } else if (this.status_cronometro_discurso === 'I') {
        this.start(1)
      }

      if (this.status_cronometro_aparte === 'S') {
        this.stop(2)
      } else if (this.status_cronometro_aparte === 'I') {
        this.start(2)
      }

      if (this.status_cronometro_ordem === 'S') {
        this.stop(3)
      } else if (this.status_cronometro_ordem === 'I') {
        this.start(3)
      }

      if (this.status_cronometro_consideracoes === 'S') {
        this.stop(4)
      } else if (this.status_cronometro_consideracoes === 'I') {
        this.start(4)
      }

      if (this.status_cronometro_personalizado === 'S') {
        this.stop(5)
      } else if (this.status_cronometro_personalizado === 'I') {
        this.start(5)
      }

      // Setar os timers no caso de nulo ou resetado
      if (time_d === null || this.status_cronometro_discurso === 'R') {
        this.setTimer(1)
        this.stop(1)
      }
      if (time_a === null || this.status_cronometro_aparte === 'R') {
        this.setTimer(2)
        this.stop(2)
      }
      if (time_o === null || this.status_cronometro_ordem === 'R') {
        this.setTimer(3)
        this.stop(3)
      }
      if (time_c === null || this.status_cronometro_consideracoes === 'R') {
        this.setTimer(4)
        this.stop(4)
      }
      if (time_p === null || this.status_cronometro_personalizado === 'R') {
        this.setTimer(5)
        this.stop(5)
      }
    },
    setTimer (temp_crono) {
      var temp
      var res
      var now
      if (temp_crono === 6) {
        // Pegar data atual
        this.cronometro_discurso = new Date()
        this.cronometro_aparte = this.cronometro_discurso
        this.cronometro_ordem = this.cronometro_discurso
        this.cronometro_consideracoes = this.cronometro_discurso
        this.cronometro_personalizado = this.cronometro_discurso

        // Setar cada Cronometro
        temp = new Date()
        temp.setSeconds(this.cronometro_discurso.getSeconds() + cronometroStart[0])
        res = new Date(temp - this.cronometro_discurso)
        res.setHours(temp.getHours() - this.cronometro_discurso.getHours())
        this.cronometro_discurso = this.formatTime(res)

        temp = new Date()
        temp.setSeconds(this.cronometro_aparte.getSeconds() + cronometroStart[1])
        res = new Date(temp - this.cronometro_aparte)
        res.setHours(temp.getHours() - this.cronometro_aparte.getHours())
        this.cronometro_aparte = this.formatTime(res)

        temp = new Date()
        temp.setSeconds(this.cronometro_ordem.getSeconds() + cronometroStart[2])
        res = new Date(temp - this.cronometro_ordem)
        res.setHours(temp.getHours() - this.cronometro_ordem.getHours())
        this.cronometro_ordem = this.formatTime(res)

        temp = new Date()
        temp.setSeconds(this.cronometro_consideracoes.getSeconds() + cronometroStart[3])
        res = new Date(temp - this.cronometro_consideracoes)
        res.setHours(temp.getHours() - this.cronometro_consideracoes.getHours())
        this.cronometro_consideracoes = this.formatTime(res)

        temp = new Date()
        temp.setSeconds(this.cronometro_personalizado.getSeconds() + cronometroStart[4])
        res = new Date(temp - this.cronometro_personalizado)
        res.setHours(temp.getHours() - this.cronometro_personalizado.getHours())
        this.cronometro_personalizado = this.formatTime(res)
      } else {
        now = new Date()
        switch (temp_crono) {
          case 1:
            time_d = null
            temp = new Date()
            temp.setSeconds(now.getSeconds() + cronometroStart[0])
            res = new Date(temp - now)
            res.setHours(cronometroStart[0] / 3600)
            this.cronometro_discurso = this.formatTime(res)
            break
          case 2:
            time_a = null
            temp = new Date()
            temp.setSeconds(now.getSeconds() + cronometroStart[1])
            res = new Date(temp - now)
            res.setHours(cronometroStart[1] / 3600)
            this.cronometro_aparte = this.formatTime(res)
            break
          case 3:
            time_o = null
            temp = new Date()
            temp.setSeconds(now.getSeconds() + cronometroStart[2])
            res = new Date(temp - now)
            res.setHours(cronometroStart[2] / 3600)
            this.cronometro_ordem = this.formatTime(res)
            break
          case 4:
            time_c = null
            temp = new Date()
            temp.setSeconds(now.getSeconds() + cronometroStart[3])
            res = new Date(temp - now)
            res.setHours(cronometroStart[3] / 3600)
            this.cronometro_consideracoes = this.formatTime(res)
            break
          case 5:
            time_p = null
            temp = new Date()
            temp.setSeconds(now.getSeconds() + cronometroStart[4])
            res = new Date(temp - now)
            res.setHours(cronometroStart[4] / 3600)
            this.cronometro_personalizado = this.formatTime(res)
        }
      }
    },
    formatTime (time) {
      var tempo = time.getHours().toLocaleString('en-US', {
        minimumIntegerDigits: 2,
        useGrouping: false
      }) + ':' + time.getMinutes().toLocaleString('en-US', {
        minimumIntegerDigits: 2,
        useGrouping: false
      }) + ':' + time.getSeconds().toLocaleString('en-US', {
        minimumIntegerDigits: 2,
        useGrouping: false
      })
      return tempo
    },
    stop: function stop (crono) {
      if (crono === 6) {
        audioAlertFinish.play()
      } else {
        this.running[crono - 1] = 0
        clearInterval(started[crono - 1])
      }
    },
    clockRunning (crono) {
      switch (crono) {
        case 1:
          if (this.status_cronometro_discurso !== 'I') return
          var now_d = new Date()
          time_d = new Date(timeEnd_d - now_d)

          // Definir propriamento o tempo
          time_d.setHours((time_d.getTime() / 1000) / 3600)

          if (timeEnd_d > now_d) {
            this.cronometro_discurso = this.formatTime(time_d)
          } else {
            audioAlertFinish.play()
            this.alert = setTimeout(() => {
              this.reset()
            }, 5000)
          }
          break
        case 2:
          if (this.status_cronometro_aparte !== 'I') return
          var now_a = new Date()
          time_a = new Date(timeEnd_a - now_a)

          // Definir propriamento o tempo
          time_a.setHours((time_a.getTime() / 1000) / 3600)

          if (timeEnd_a > now_a) {
            this.cronometro_aparte = this.formatTime(time_a)
          } else {
            audioAlertFinish.play()
            this.alert = setTimeout(() => {
              this.reset()
            }, 5000)
          }
          break
        case 3:
          if (this.status_cronometro_ordem !== 'I') return
          var now_o = new Date()
          time_o = new Date(timeEnd_o - now_o)

          // Definir propriamento o tempo
          time_o.setHours((time_o.getTime() / 1000) / 3600)

          if (timeEnd_o > now_o) {
            this.cronometro_ordem = this.formatTime(time_o)
          } else {
            audioAlertFinish.play()
            this.alert = setTimeout(() => {
              this.reset()
            }, 5000)
          }
          break
        case 4:
          if (this.status_cronometro_consideracoes !== 'I') return
          var now_c = new Date()
          time_c = new Date(timeEnd_c - now_c)

          // Definir propriamento o tempo
          time_c.setHours((time_c.getTime() / 1000) / 3600)

          if (timeEnd_c > now_c) {
            this.cronometro_consideracoes = this.formatTime(time_c)
          } else {
            audioAlertFinish.play()
            this.alert = setTimeout(() => {
              this.reset()
            }, 5000)
          }
          break
        case 5:
          if (this.status_cronometro_personalizado !== 'I') return
          var now_p = new Date()
          time_p = new Date(timeEnd_p - now_p)

          // Definir propriamento o tempo
          time_p.setHours((time_p.getTime() / 1000) / 3600)

          if (timeEnd_p > now_p) {
            this.cronometro_personalizado = this.formatTime(time_p)
          } else {
            audioAlertFinish.play()
            this.alert = setTimeout(() => {
              this.reset()
            }, 5000)
          }
          break
      }
    },
    start: function startStopWatch (temp_crono) {
      if (this.running[temp_crono - 1] === 1) return

      switch (temp_crono) {
        case 1:
          if (time_d === null) {
            time_d = cronometroStart[0]
            timeEnd_d = new Date()
            timeEnd_d.setSeconds(timeEnd_d.getSeconds() + time_d)
          } else {
            timeEnd_d = new Date()
            timeEnd_d.setHours(timeEnd_d.getHours() + time_d.getHours())
            timeEnd_d.setMinutes(timeEnd_d.getMinutes() + time_d.getMinutes())
            timeEnd_d.setSeconds(timeEnd_d.getSeconds() + time_d.getSeconds())
          }
          this.running[0] = 1

          started[0] = setInterval(() => {
            this.clockRunning(temp_crono)
          }, 50)
          break
        case 2:
          if (time_a === null) {
            time_a = cronometroStart[1]
            timeEnd_a = new Date()
            timeEnd_a.setSeconds(timeEnd_a.getSeconds() + time_a)
          } else {
            timeEnd_a = new Date()
            timeEnd_a.setHours(timeEnd_a.getHours() + time_a.getHours())
            timeEnd_a.setMinutes(timeEnd_a.getMinutes() + time_a.getMinutes())
            timeEnd_a.setSeconds(timeEnd_a.getSeconds() + time_a.getSeconds())
          }
          this.running[1] = 1

          started[1] = setInterval(() => {
            this.clockRunning(temp_crono)
          }, 50)
          break
        case 3:
          if (time_o === null) {
            time_o = cronometroStart[2]
            timeEnd_o = new Date()
            timeEnd_o.setSeconds(timeEnd_o.getSeconds() + time_o)
          } else {
            timeEnd_o = new Date()
            timeEnd_o.setHours(timeEnd_o.getHours() + time_o.getHours())
            timeEnd_o.setMinutes(timeEnd_o.getMinutes() + time_o.getMinutes())
            timeEnd_o.setSeconds(timeEnd_o.getSeconds() + time_o.getSeconds())
          }
          this.running[2] = 1

          started[2] = setInterval(() => {
            this.clockRunning(temp_crono)
          }, 50)
          break
        case 4:
          if (time_c === null) {
            time_c = cronometroStart[3]
            timeEnd_c = new Date()
            timeEnd_c.setSeconds(timeEnd_c.getSeconds() + time_c)
          } else {
            timeEnd_c = new Date()
            timeEnd_c.setHours(timeEnd_c.getHours() + time_c.getHours())
            timeEnd_c.setMinutes(timeEnd_c.getMinutes() + time_c.getMinutes())
            timeEnd_c.setSeconds(timeEnd_c.getSeconds() + time_c.getSeconds())
          }
          this.running[3] = 1

          started[3] = setInterval(() => {
            this.clockRunning(temp_crono)
          }, 50)
          break
        case 5:
          if (time_p === null) {
            time_p = cronometroStart[4]
            timeEnd_p = new Date()
            timeEnd_p.setSeconds(timeEnd_p.getSeconds() + time_p)
          } else {
            timeEnd_p = new Date()
            timeEnd_p.setHours(timeEnd_p.getHours() + time_p.getHours())
            timeEnd_p.setMinutes(timeEnd_p.getMinutes() + time_p.getMinutes())
            timeEnd_p.setSeconds(timeEnd_p.getSeconds() + time_p.getSeconds())
          }
          this.running[4] = 1

          started[4] = setInterval(() => {
            this.clockRunning(temp_crono)
          }, 50)
          break
      }
    },
    atualizaRelogio: function atualizaRelogio () {
      this.relogio = this.formatTime(new Date())
    }
  },
  created () {
    socket.onopen = function (e) {
      console.log('Connection established')

      // Pedir os dados uma vez
      var id = window.location.href.slice(-3)
      if (isNaN(id.charAt(0)) === true) {
        id = window.location.href.slice(-2)
        if (isNaN(id.charAt(0)) === true) {
          id = window.location.href.slice(-1)
        }
      }
      socket.send(id)
    }

    const _this = this

    socket.onmessage = function (e) {
      _this.teste = JSON.parse(e.data)
      _this.fetchData()
      console.log('Data Received...')
    }

    socket.onclose = function (e) {
      console.error('Ws fechou!')
    }
  }
})
