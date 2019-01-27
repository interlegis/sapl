let _$ = window.$
let JsDiff = require('diff')

function isElementInViewport (el) {
  if (typeof jQuery === 'function' && el instanceof jQuery) {
    el = el[0]
  }

  let rect = el.getBoundingClientRect()

  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <=
      (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  )
}

function textoMultiVigente (item, diff) {
  let elv = null
  let ldpts = _$('.dptt')
  for (let i = 0; i < ldpts.length; i++) {
    if (_$(ldpts[i]).hasClass('displaynone')) continue
    if (isElementInViewport(ldpts[i])) {
      if (i + 1 < ldpts.length) elv = ldpts[i + 1]
      else {
        elv = ldpts[i]
      }
      break
    }
  }

  _$('.cp .tipo-vigencias a').removeClass('selected')
  _$(item).addClass('selected')
  _$('.dptt.desativado').removeClass('displaynone')
  _$('.dtxt').removeClass('displaynone')
  _$('.dtxt.diff').remove()
  _$('.nota-alteracao').removeClass('displaynone')

  if (diff) {
    _$('.dtxt[id^="da"').each(function () {
      if (_$(this)
        .html()
        .search(/<\/\w+>/g) > 0) {
        return
      }

      let pk = _$(this).attr('pk')
      let pks = _$(this).attr('pks')

      let a = _$('#d' + pks)
        .contents()
        .filter(function () {
          return this.nodeType === Node.TEXT_NODE
        })
      let b = _$('#da' + pk)
        .contents()
        .filter(function () {
          return this.nodeType === Node.TEXT_NODE
        })

      let diff = JsDiff.diffWordsWithSpace(_$(a).text(), _$(b).text())

      if (diff.length > 0) {
        _$('#d' + pks)
          .closest('.desativado')
          .addClass('displaynone')

        let clone = _$('#da' + pk).clone()
        _$('#da' + pk).after(clone)
        _$('#da' + pk).addClass('displaynone')
        _$(clone)
          .addClass('diff')
          .html('')

        diff.forEach(function (part) {
          // let color = part.added ? '#018' : part.removed ? '#faa' : ''

          let span = document.createElement('span')

          let value = part.value

          if (part.removed) {
            _$(span).addClass('desativado')
            value += ' '
          } else if (part.added) {
            _$(span).addClass('added')
          }

          span.appendChild(document.createTextNode(value))
          _$(clone).append(span)
        })
      }
    })
    // textoVigente(item, true)
  }

  if (elv) {
    try {
      _$('html, body').animate(
        {
          scrollTop:
            _$(elv)
              .parent()
              .offset().top - 60
        },
        0
      )
    } catch (err) {
      console.log(err)
    }
  }
}

function textoVigente (item, link) {
  let elv = null
  let ldpts = _$('.dptt')
  for (let i = 0; i < ldpts.length; i++) {
    if (_$(ldpts[i]).hasClass('displaynone')) continue
    if (isElementInViewport(ldpts[i])) {
      if (i + 1 < ldpts.length) elv = ldpts[i + 1]
      else {
        elv = ldpts[i]
      }
      break
    }
  }

  _$('.cp .tipo-vigencias a').removeClass('selected')
  _$(item).addClass('selected')

  _$('.dptt.desativado').addClass('displaynone')
  _$('.nota-alteracao').removeClass('displaynone')
  if (!link) _$('.nota-alteracao').addClass('displaynone')

  if (elv) {
    try {
      _$('html, body').animate(
        {
          scrollTop:
            _$(elv)
              .parent()
              .offset().top - 60
        },
        0
      )
    } catch (err) {
      console.log(err)
    }
  }
}

export default {
  isElementInViewport,
  textoMultiVigente,
  textoVigente
}
