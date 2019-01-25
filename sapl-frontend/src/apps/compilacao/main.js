// TODO: migrar compilacao para VueJs

import './scss/compilacao.scss'

import 'bootstrap'

import compilacao from './js/old/compilacao'
import compilacaoView from './js/old/compilacao_view'
import compilacaoNotas from './js/old/compilacao_notas'

// import './js/compilacao_edit'

_.forEach(_.merge(_.merge(compilacao, compilacaoNotas), compilacaoView), function (func, key) {
  window[key] = func
})

$(document).ready(function () {
  setTimeout(function () {
    var href = location.href.split('#')
    if (href.length === 2) {
      try {
        $('html, body').animate(
          {
            scrollTop:
              $('#dptt' + href[1]).offset().top - window.innerHeight / 9
          },
          0
        )
      } catch (err) {
        console.log(err)
      }
    }
  }, 100)

  $('#btn_font_menos').click(function () {
    $('.dpt').css('font-size', '-=1')
  })
  $('#btn_font_mais').click(function () {
    $('.dpt').css('font-size', '+=1')
  })

  $('.dpt.bloco_alteracao .dpt').each(function () {
    var nivel = parseInt($(this).attr('nivel'))
    $(this).css('z-index', 15 - nivel)
  })
  window.onReadyNotasVides()
})
