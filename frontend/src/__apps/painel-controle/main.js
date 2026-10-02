import './scss/painel.scss'
import Vue from 'vue'
import { FormSelectPlugin } from 'bootstrap-vue'
import axios from 'axios'

//TODO: incluir painel-controle dentro da app de painel, colocando rotas diferentes

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'

Vue.use(FormSelectPlugin)

console.log('painel controle main.js carregado')

const v = new Vue({ // eslint-disable-line
  delimiters: ['[[', ']]'],
  el: '#painel-controle',
  data () {
    return {
      sessao_plenaria: "74ª Sessão Ordinária da 1ª Sessão Legislativa da 18ª Legislatura",
      message: "",
    }
  },

  watch: {},

  computed: {

  },

  created () {},

  methods: {},

  mounted () {
    console.log("Painel controle app mounted!")
  }
})
