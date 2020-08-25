import './scss/parlamentar.scss'
import Vue from 'vue'
import { FormSelectPlugin } from 'bootstrap-vue'
import axios from 'axios'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(FormSelectPlugin)

const v = new Vue({ // eslint-disable-line
  delimiters: ['[[', ']]'],
  el: '#app2',
  data () {
    return {
      nome_pesquisa: '',
      is_pesquisa: false,
      legislatura_selecionada: '',
      legislaturas: [],
      parlamentares: [],
      visible_parlamentares: [],
      size_parlamentares: 0,
      filter_ativo: false,
      filter_titular: ''
    }
  },

  watch: {
    nome_pesquisa: function (val) {
      this.debouncepesquisaParlamentar()
    }
  },

  created () {
    this.debouncepesquisaParlamentar = _.debounce(this.pesquisaParlamentar, 500)
  },

  methods: {
    getParlamentares (event) {
      if (this.legislatura_selecionada || this.legislatura_selecionada.toString() === '0') {
        axios.get('/api/parlamentares/parlamentar/' + this.legislatura_selecionada + '/parlamentares_by_legislatura/')
          .then(response => {
            this.parlamentares = response.data
            this.visible_parlamentares = this.parlamentares
            this.size_parlamentares = this.visible_parlamentares.length
            this.checkTitularAtivo()
          })
          .catch(error => {
            console.error('Ocorreu um erro ao obter os dados de parlamentares:' + error)
          })
      }
    },

    pesquisaParlamentar (event) {
      axios.get('/api/parlamentares/parlamentar/search_parlamentares/', {
        params: { nome_parlamentar: this.nome_pesquisa }
      })
        .then(response => {
          this.parlamentares = response.data
          this.visible_parlamentares = this.parlamentares
          this.size_parlamentares = this.visible_parlamentares.length
        })
        .catch(error => {
          console.error('Erro ao procurar parlamentar:' + error)
        })
    },

    checkTitularAtivo (event) {
      this.visible_parlamentares = this.parlamentares
      if (this.filter_ativo) {
        this.visible_parlamentares = this.visible_parlamentares.filter((v) => v.ativo)
      }
      if (this.filter_titular) {
        this.visible_parlamentares = this.visible_parlamentares.filter((v) => v.titular === 'Sim')
      }
      this.size_parlamentares = this.visible_parlamentares.length
    },

    pesquisaChange (event) {
      this.is_pesquisa = !this.is_pesquisa
      this.filter_ativo = false
      if (this.is_pesquisa) {
        this.parlamentares = []
      } else {
        this.getParlamentares()
      }
    }
  },

  mounted () {
    axios.get('/api/parlamentares/legislatura/?get_all=true')
      .then(response => {
        this.legislaturas = response.data
        this.legislatura_selecionada = response.data[0].id
      })
      .then(response => {
        this.getParlamentares()
      })
      .catch(err => {
        console.error('Ocorreu um erro ao obter os dados de legislação: ' + err)
      })
  }
})
