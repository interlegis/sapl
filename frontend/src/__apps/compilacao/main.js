// TODO: migrar compilacao para VueJs

import './scss/compilacao.scss'

import compilacao from './js/old/compilacao'
import compilacaoView from './js/old/compilacao_view'
import compilacaoNotas from './js/old/compilacao_notas'

import './js/old/compilacao_edit'

_.forEach(_.merge(_.merge(compilacao, compilacaoNotas), compilacaoView), function (func, key) {
  window[key] = func
})

$(document).ready(function () {
  window.InitViewTAs()
  window.onReadyNotasVides()
})
