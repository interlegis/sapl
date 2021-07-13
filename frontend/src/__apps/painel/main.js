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
      oradores: []
    }
  },
  methods: {

    atribuiColor (parlamentar) {
      var color = 'white'
      if (parlamentar.voto === 'Voto Informado') {
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
    fetchData () {
      // TODO: how to get no hardcoded URL?
      $.get('/painel/704/dados', function (response) {
        this.brasao = response.brasao
        this.painel_aberto = response.status_painel
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
      }.bind(this))
    },
    pollData () {
      this.fetchData()

      this.polling = setInterval(() => {
        console.info('Fetching data from backend')
        this.fetchData()
      }, 500)
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
