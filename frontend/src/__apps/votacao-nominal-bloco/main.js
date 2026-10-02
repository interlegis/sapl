import './scss/votacao-nominal-bloco.scss'
import Vue from 'vue'

import VotacaoNominalBloco from '../../components/votacao-nominal-bloco/VotacaoNominalBloco.vue'

Vue.component('votacao-nominal-bloco', VotacaoNominalBloco)

// Sem Pinia/WebSocket aqui de propósito: este formulário é preenchido e
// submetido de uma vez (POST nativo pra VotacaoEmBlocoNominalView, que
// continua sem mudanças), não uma tela de estado ao vivo — a única coisa
// que precisava parar de usar polling era a soma dos votos, que já vira
// reatividade normal do Vue dentro de VotacaoNominalBloco.vue.
const parlamentaresEl = document.getElementById('parlamentares-data')
let parlamentares = []
if (parlamentaresEl) {
  try {
    parlamentares = JSON.parse(parlamentaresEl.textContent)
  } catch (e) {
    console.error('Erro ao ler parlamentares-data:', e)
  }
}

new Vue({ // eslint-disable-line
  el: '#app-votacao-nominal-bloco',
  data () {
    return { parlamentares }
  }
})
