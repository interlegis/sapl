import './scss/painel.scss'
import Vue from 'vue'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

//  Variaveis dos cronometros
var crono = 0
var time = null
var timeEnd = null
var audioAlertFinish = document.getElementById('audio')
var cronometroStart = []
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
      mat_em_votacao: '',
      resultado_votacao_css: '',
      tipo_resultado: '',
      tipo_votacao: '',
      teste: null,
      running: 0,
      status_cronometro_discurso: ''
    }
  },
  methods: {
    msgMateria () {
      if (this.tipo_resultado && this.painel_aberto) {
        if (this.tipo_votacao !== 'Leitura' && !this.sessao_finalizada && !this.sessao_solene) {
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
      this.status_cronometro_discurso = objeto.status_cronometro

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
      this.mat_em_votacao = this.msgMateria()

      // Cronometros
      cronometroStart[0] = objeto.cronometro_discurso
      cronometroStart[1] = objeto.cronometro_aparte
      cronometroStart[2] = objeto.cronometro_ordem
      cronometroStart[3] = objeto.cronometro_consideracoes

      this.setTimer()

      if (this.status_cronometro_discurso === 'I') {
        this.start(1)
      } else if (this.status_cronometro_discurso === 'S') {
        this.stop(1)
      }
    },
    setTimer () {
      if (time === null) {
        // Pegar data atual
        this.cronometro_discurso = new Date()
        this.cronometro_aparte = this.cronometro_discurso
        this.cronometro_ordem = this.cronometro_discurso
        this.cronometro_consideracoes = this.cronometro_discurso

        // Setar cada Cronometro
        var temp = new Date()
        temp.setSeconds(this.cronometro_discurso.getSeconds() + cronometroStart[0])
        var res = new Date(temp - this.cronometro_discurso)
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
      if (crono === 5) {
        audioAlertFinish.play()
      }

      this.running = 0
      clearInterval(this.started)
      console.log(time)
    },
    reset: function reset () {
      this.running = 0
      time = null
      clearInterval(this.started)
      clearInterval(this.stopped)

      this.setTimer()
    },
    clockRunning (crono) {
      var now = new Date()
      time = new Date(timeEnd - now)

      // Definir propriamento o tempo
      time.setHours(timeEnd.getHours() - now.getHours())

      if (timeEnd > now) {
        if (crono === 1) {
          this.cronometro_discurso = this.formatTime(time)
        } else if (crono === 2) {
          this.cronometro_aparte = this.formatTime(time)
        } else if (crono === 3) {
          this.cronometro_ordem = this.formatTime(time)
        } else {
          this.cronometro_consideracoes = this.formatTime(time)
        }
      } else {
        audioAlertFinish.play()
        this.alert = setTimeout(() => {
          this.reset()
        }, 5000)
      }
    },
    start: function startStopWatch (temp_crono) {
      if (this.running === temp_crono) return

      crono = temp_crono
      if (time === null) {
        time = cronometroStart[crono - 1]
        timeEnd = new Date()
        timeEnd.setSeconds(timeEnd.getSeconds() + time)
        console.log(timeEnd)
      } else {
        timeEnd = new Date()
        timeEnd.setMinutes(timeEnd.getMinutes() + time.getMinutes())
        timeEnd.setSeconds(timeEnd.getSeconds() + time.getSeconds())
        timeEnd.setMilliseconds(timeEnd.getMilliseconds() + time.getMilliseconds())
      }
      this.running = crono

      this.started = setInterval(() => {
        this.clockRunning(crono)
      }, 50)
    }
  },
  created () {
    socket.onopen = function (e) {
      console.log('Connection established')

      // Pedir os dados uma vez
      const id = window.location.href.slice(-3)
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
