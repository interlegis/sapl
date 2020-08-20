
const _$ = window.$

function onEventsDneExec (pk, model) {
  _$('html, body').animate({
    scrollTop: _$('#dne' + pk).offset().top - window.innerHeight / 5
  }, 300)

  window.refreshDatePicker()

  _$('#dne' + pk + ' #button-id-submit-form').click(onSubmitEditNVForm)
  _$('#dne' + pk + ' .btn-close-container').click(function () {
    _$(this).closest('.dne-nota').removeClass('dne-nota')
    _$(this).closest('.dne-form').html('')
  })

  if (model === 'nota') {
    _$('#dne' + pk + ' select[name="tipo"]').change(function (event) {
      let url = ''
      url = 'text/' + pk + '/nota/create?action=modelo_nota&id_tipo=' + this.value
      _$.get(url).done(function (data) {
        _$('#dne' + pk + ' textarea[name="texto"]').val(data)
      })
    })
  } else if (model === 'vide') {
    window.DispositivoSearch({
      url_form: '/ta/search_form',
      text_button: 'Definir Dispositivo'
    })
  }
}

function onSubmitEditNVForm (event) {
  let url = ''
  let model = 'nota'
  let idEdit = null
  let idDispositivo = _$('#id_dispositivo').val()

  if (idDispositivo === undefined) { // trata-se de um vide
    // _$('#idDispositivo_ref').remove()
    idDispositivo = _$('#id_dispositivo_base').val()
    model = 'vide'
  }

  idEdit = _$('#id_pk').val()
  url = 'text/' + idDispositivo + '/' + model + '/'
  if (idEdit === null || idEdit === '') {
    url += 'create'
  } else {
    url += idEdit + '/edit'
  }

  // console.log(_$('#dne' + idDispositivo + ' form').serialize())

  _$.post(url, _$('#dne' + idDispositivo + ' form').serialize(), function (data) {
    if (typeof data === 'string') {
      if (data.indexOf('<form') >= 0) {
        _$('#dne' + idDispositivo + ' .dne-form').html(data)
        onEventsDneExec(idDispositivo, model)
      } else {
        _$('#dne' + idDispositivo + ' .dne-form').closest('.dpt').html(data)
        onReadyNotasVides()
        try {
          _$('html, body').animate({
            scrollTop: _$('#dne' + idDispositivo).offset().top - window.innerHeight / 3
          }, 300)
        } catch (err) {
        }
      }
    }
  })
}

function onDelete (event) {
  const model = _$(event).attr('model')

  const idDispositivo = _$(event).closest('.dn').attr('pk')
  const idDelete = _$(event).attr('pk')
  const url = 'text/' + idDispositivo + '/' + model + '/' + idDelete + '/delete'

  _$.get(url, function (data) {
    _$('#dne' + idDispositivo + ' .dne-form').closest('.dpt').html(data)
    onReadyNotasVides()
  })
}

function getForm (_this) {
  let url = ''
  const model = _$(_this).attr('model')
  let idDispositivo = _$('.dne-nota .dne-form').closest('.dne').attr('pk')
  if (idDispositivo != null) {
    _$('#dne' + idDispositivo).removeClass('dne-nota')
    _$('#dne' + idDispositivo + ' .dne-form').html('')
  }

  if (_this.className.indexOf('create') >= 0) {
    idDispositivo = _$(_this).attr('pk')
    url = 'text/' + idDispositivo + '/' + model + '/create'
  } else if (_this.className.indexOf('edit') >= 0) {
    const idEdit = _$(_this).attr('pk')
    idDispositivo = _$(_this).closest('.dn').attr('pk')
    url = 'text/' + idDispositivo + '/' + model + '/' + idEdit + '/edit'
  }

  _$('#dne' + idDispositivo).addClass('dne-nota')

  _$.get(url).done(function (data) {
    _$('#dne' + idDispositivo + ' .dne-form').html(data)
    onEventsDneExec(idDispositivo, model)
  }).fail(function () {
    onReadyNotasVides()
  })
}

function onReadyNotasVides () {
  _$('.dne-nota').removeClass('dne-nota')
  _$('.dne-form').html('')

  _$('.dne .btn-action').off()
  _$('.dn .btn-action').off()

  _$('.dne .btn-action, .dn .btn-action').not('.btn-nota-delete').not('.btn-vide-delete').click(function () {
    getForm(this)
  })

  _$('.dn .btn-nota-delete, .dn .btn-vide-delete').click(function () {
    onDelete(this)
  })
}

export default {
  onEventsDneExec,
  onSubmitEditNVForm,
  onDelete,
  onReadyNotasVides
}
