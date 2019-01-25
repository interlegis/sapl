
function onEventsDneExec (pk, model) {
  $('html, body').animate({
    scrollTop: $('#dne' + pk).offset().top - window.innerHeight / 5
  }, 300)

  window.refreshDatePicker()

  $('#dne' + pk + ' #button-id-submit-form').click(onSubmitEditNVForm)
  $('#dne' + pk + ' .btn-close-container').click(function () {
    $(this).closest('.dne-nota').removeClass('dne-nota')
    $(this).closest('.dne-form').html('')
  })

  if (model === 'nota') {
    $('#dne' + pk + ' select[name="tipo"]').change(function (event) {
      let url = ''
      url = 'text/' + pk + '/nota/create?action=modelo_nota&id_tipo=' + this.value
      $.get(url).done(function (data) {
        $('#dne' + pk + ' textarea[name="texto"]').val(data)
      })
    })
  } else if (model === 'vide') {
    window.DispositivoSearch({
      'url_form': '/ta/search_form',
      'text_button': 'Definir Dispositivo'
    })
  }
}

function onSubmitEditNVForm (event) {
  let url = ''
  let model = 'nota'
  let idEdit = null
  let idDispositivo = $('#idDispositivo').val()

  if (idDispositivo === null) { // trata-se de um vide
    // $('#idDispositivo_ref').remove()
    idDispositivo = $('#idDispositivo_base').val()
    model = 'vide'
  }

  idEdit = $('#id_pk').val()
  url = 'text/' + idDispositivo + '/' + model + '/'
  if (idEdit === null || idEdit === '') {
    url += 'create'
  } else {
    url += idEdit + '/edit'
  }

  console.log($('#dne' + idDispositivo + ' form').serialize())

  $.post(url, $('#dne' + idDispositivo + ' form').serialize(), function (data) {
    if (typeof data === 'string') {
      if (data.indexOf('<form') >= 0) {
        $('#dne' + idDispositivo + ' .dne-form').html(data)
        onEventsDneExec(idDispositivo, model)
      } else {
        $('#dne' + idDispositivo + ' .dne-form').closest('.dpt').html(data)
        onReadyNotasVides()
        try {
          $('html, body').animate({
            scrollTop: $('#dne' + idDispositivo).offset().top - window.innerHeight / 3
          }, 300)
        } catch (err) {
        }
      }
    }
  })
}

function onDelete (event) {
  let model = $(event).attr('model')

  let idDispositivo = $(event).closest('.dn').attr('pk')
  let idDelete = $(event).attr('pk')
  let url = 'text/' + idDispositivo + '/' + model + '/' + idDelete + '/delete'

  $.get(url, function (data) {
    $('#dne' + idDispositivo + ' .dne-form').closest('.dpt').html(data)
    onReadyNotasVides()
  })
}

function getForm (_this) {
  let url = ''
  let model = $(_this).attr('model')
  let idDispositivo = $('.dne-nota .dne-form').closest('.dne').attr('pk')
  if (idDispositivo != null) {
    $('#dne' + idDispositivo).removeClass('dne-nota')
    $('#dne' + idDispositivo + ' .dne-form').html('')
  }

  if (_this.className.indexOf('create') >= 0) {
    idDispositivo = $(_this).attr('pk')
    url = 'text/' + idDispositivo + '/' + model + '/create'
  } else if (_this.className.indexOf('edit') >= 0) {
    let idEdit = $(_this).attr('pk')
    idDispositivo = $(_this).closest('.dn').attr('pk')
    url = 'text/' + idDispositivo + '/' + model + '/' + idEdit + '/edit'
  }

  $('#dne' + idDispositivo).addClass('dne-nota')

  $.get(url).done(function (data) {
    $('#dne' + idDispositivo + ' .dne-form').html(data)
    onEventsDneExec(idDispositivo, model)
  }).fail(function () {
    onReadyNotasVides()
  })
}

function onReadyNotasVides () {
  $('.dne-nota').removeClass('dne-nota')
  $('.dne-form').html('')

  $('.dne .btn-action').off()
  $('.dn .btn-action').off()

  $('.dne .btn-action, .dn .btn-action').not('.btn-nota-delete').not('.btn-vide-delete').click(function () {
    getForm(this)
  })

  $('.dn .btn-nota-delete, .dn .btn-vide-delete').click(function () {
    onDelete(this)
  })
}

export default {
  onEventsDneExec,
  onSubmitEditNVForm,
  onDelete,
  onReadyNotasVides
}
