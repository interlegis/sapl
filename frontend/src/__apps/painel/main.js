import './scss/painel.scss'
import Vue from 'vue'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

const v = new Vue({ // eslint-disable-line
  delimiters: ['[[', ']]'],
  el: '#app-painel',
  data () {
    return {
      message: 'Hello VueJUS', // TODO: remove when porting to VueJS is done
      polling: null,
      painel_aberto: true,
      sessao_plenaria: '',
      sessao_plenaria_data: '',
      sessao_plenaria_hora_inicio: '',
      brasao: '',
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
      tipo_votacao: ''
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
      $.get('/painel/2867/dados', function (response) {
        this.brasao = response.brasao
        this.painel_aberto = response.status_painel
        this.sessao_finalizada = response.sessao_finalizada
        this.sessao_plenaria = response.sessao_plenaria
        this.sessao_plenaria_data = 'Data Início: ' + response.sessao_plenaria_data
        this.sessao_plenaria_hora_inicio = 'Hora Início: ' + response.sessao_plenaria_hora_inicio
        this.sessao_solene = response.sessao_solene
        this.sessao_solene_tema = response.sessao_solene_tema

        this.presentes = response.presentes
        this.presentes.forEach(parlamentar => {
          this.atribuiColor(parlamentar)
        })

        this.oradores = response.oradores

        this.materia_legislativa_texto = response.materia_legislativa_texto
        this.numero_votos_sim = response.numero_votos_sim
        this.numero_votos_nao = response.numero_votos_nao
        this.numero_abstencoes = response.numero_abstencoes
        this.num_presentes = response.num_presentes
        this.total_votos = response.total_votos

        this.materia_legislativa_texto = response.materia_legislativa_texto
        this.materia_legislativa_ementa = response.materia_legislativa_ementa
        this.observacao_materia = this.capObservacao(response.observacao_materia)

        this.tipo_resultado = response.tipo_resultado
        this.tipo_votacao = response.tipo_votacao
        this.mat_em_votacao = this.msgMateria()
      }.bind(this))
    },
    pollData () {
      this.fetchData()

      this.polling = setInterval(() => {
        console.info('Fetching data from backend')
        this.fetchData()
      }, 5000)
    }
  },
  beforeDestroy () {
    console.info('Destroying polling.')
    clearInterval(this.polling)
  },
  created () {
    console.info('Start polling data...')
    this.pollData()
  }
})
