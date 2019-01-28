let _$ = window.$

function SetCookie (cookieName, cookieValue, nDays) {
  let today = new Date()
  let expire = new Date()
  if (nDays === null || nDays === 0) nDays = 1
  expire.setTime(today.getTime() + 3600000 * 24 * nDays)
  document.cookie = cookieName + '=' + escape(cookieValue) +
    ';expires=' + expire.toGMTString()
}

function ReadCookie (cookieName) {
  let theCookie = ' ' + document.cookie
  let ind = theCookie.indexOf(' ' + cookieName + '=')
  if (ind === -1) ind = theCookie.indexOf(';' + cookieName + '=')
  if (ind === -1 || cookieName === '') return ''
  let ind1 = theCookie.indexOf(';', ind + 1)
  if (ind1 === -1) ind1 = theCookie.length
  return unescape(theCookie.substring(ind + cookieName.length + 2, ind1))
}

function insertWaitAjax (element) {
  // jQuery(element).append('<div style="text-align:center;'><img src="/static/img/ajax-loader.gif'></div>')
  _$(element).append('<div style="text-align:center;"><i style="font-size: 200%;" class="fa fa-refresh fa-spin"></i></div>')
}

function DispositivoSearch (opts) {
  _$(function () {
    let formData = {}
    let containerDs = _$('body').children('#container_ds')
    if (containerDs.length > 0) {
      _$(containerDs).remove()
    }
    containerDs = _$('<div id="container_ds"/>')
    _$('body').prepend(containerDs)

    let fields = _$('[data-sapl-ta="DispositivoSearch"]')
    fields.each(function () {
      let field = _$(this)
      let dataTypeSelection = field.attr('data-type-selection')
      let dataField = field.attr('data-field')
      let dataFunction = field.attr('data-function')

      let onChangeFieldSelects = function (event) {
        if (dataTypeSelection === 'checkbox') {
          let tas = field.find('input[name="ta_select_all"]') // tas - Textos Articulados
          tas.off()

          tas.on('change', function (event) {
            _$(this).closest('ul').find('input[name="' + dataField + '"]').prop('checked', this.checked)
            // _$(this).prop('checked', false)
          })
        } else {
          let dpts = field.find('input')
          dpts.off()
          dpts.attr('type', 'hidden')
          _$('<a class="text-danger">')
            .insertBefore(dpts)
            .append(_$('<span aria-hidden="true">&times;</span>'))
            .on('click', function () {
              if (_$(this).closest('ul').find('li').length === 2) {
                _$(this).closest('ul').remove()
              } else {
                _$(this).closest('li').remove()
              }
            })
        }
      }
      onChangeFieldSelects()

      let onChangeParamTA = function (event) {
        let tipoTa = _$('select[name="tipo_ta"]').val()
        let tipoModel = _$('select[name="tipo_model"]').val()
        let numTa = _$('input[name="num_ta"]').val()
        let anoTa = _$('input[name="ano_ta"]').val()
        let dispositivosInternos = _$('input[name="dispositivos_internos"]:checked').val()
        let rotuloDispositivo = _$('input[name="rotulo_dispositivo"]').val()
        let textoDispositivo = _$('input[name="texto_dispositivo"]').val()
        let maxResults = _$('select[name="max_results"]').val()
        let url = ''

        if (rotuloDispositivo.length > 0 || textoDispositivo.length > 0) {
          _$('input[name="dispositivos_internos"]').prop('disabled', false)
          _$('input[name="dispositivos_internos"]').each((idx, element) => {
            element.parentElement.classList.remove('disabled')
          })
          _$('input[name="dispositivos_internos"]').closest('#div_id_dispositivos_internos').css('opacity', '1')
        } else {
          _$('input[name="dispositivos_internos"]').filter('[value="False"]').prop('checked', true)
          _$('input[name="dispositivos_internos"]').prop('disabled', true)

          _$('input[name="dispositivos_internos"]').each((idx, element) => {
            element.parentElement.classList.add('disabled')
          })
          _$('input[name="dispositivos_internos"]').closest('#div_id_dispositivos_internos').css('opacity', '0.3')
          dispositivosInternos = 'False'
        }
        formData = {
          'tipo_ta': tipoTa,
          'tipo_model': tipoModel,
          'num_ta': numTa,
          'ano_ta': anoTa,
          'texto': textoDispositivo,
          'rotulo': rotuloDispositivo,
          'dispositivos_internos': dispositivosInternos,
          'max_results': maxResults,
          'data_type_selection': dataTypeSelection,
          'data_field': dataField,
          'data_function': dataFunction
        }

        window.localStorage.setItem('dispositivo_search_form_data', JSON.stringify(formData))

        url = '/ta/search_fragment_form'
        _$('.result-busca-dispositivo').html('')
        insertWaitAjax('.result-busca-dispositivo')
        _$.get(url, formData).done(function (data) {
          _$('.result-busca-dispositivo').html(data)
          // OptionalCustomFrontEnd().init()
          if (dataTypeSelection === 'checkbox') {
            let tas = _$('.result-busca-dispositivo').find('input[name="ta_select_all"]')
            tas.off()
            tas.on('change', function (event) {
              _$(this).closest('ul').find('input[name="' + dataField + '"]').prop('checked', this.checked)
            })
          }
        })
      }

      let onKeyPressRotuloBuscaTextual = function (event) {
        let rotuloDispositivo = _$('input[name="rotulo_dispositivo"]').val()
        let textoDispositivo = _$('input[name="texto_dispositivo"]').val()
        // let dispositivosInternos = _$('input[name="dispositivos_internos"]:checked').val()

        if (rotuloDispositivo.length > 0 || textoDispositivo.length > 0) {
          _$('input[name="dispositivos_internos"]').prop('disabled', false)
          _$('input[name="dispositivos_internos"]').each((idx, element) => {
            element.parentElement.classList.remove('disabled')
          })
          _$('input[name="dispositivos_internos"]').closest('#div_id_dispositivos_internos').css('opacity', '1')
        } else {
          _$('input[name="dispositivos_internos"]').filter('[value="False"]').prop('checked', true)
          _$('input[name="dispositivos_internos"]').prop('disabled', true)
          _$('input[name="dispositivos_internos"]').each((idx, element) => {
            element.parentElement.classList.add('disabled')
          })
          _$('input[name="dispositivos_internos"]').closest('#div_id_dispositivos_internos').css('opacity', '0.3')
          // dispositivosInternos = 'False'
        }
      }

      let buttonDs = field.children('#buttonDs')
      if (buttonDs.length > 0) {
        _$(buttonDs).remove()
      }
      buttonDs = _$('<div id="buttonDs" class="clearfix"/>')
      field.prepend(buttonDs)

      let btnOpenSearch = _$('<button>')
        .text(opts['text_button'])
        .attr('type', 'button')
        .attr('class', 'btn btn-sm btn-success btn-modal-open')
      buttonDs.append(btnOpenSearch)
      btnOpenSearch.on('click', function () {
        _$.get(opts['url_form'], function (data) {
          containerDs.html(data)
          let modalDs = _$('#modal-ds')
          // OptionalCustomFrontEnd().init()

          modalDs.find('select[name="tipo_ta"]').change(function (event) {
            let url = ''
            url = '/ta/search_fragment_form?action=get_tipos&tipo_ta=' + this.value
            modalDs.find('label[for="id_tipo_model"]').html('Tipos de ' + this.children[this.selectedIndex].innerHTML)

            let select = modalDs.find('select[name="tipo_model"]')
            select.empty()
            _$('<option value="">Carregando...</option>').appendTo(select)

            _$.get(url).done(function (data) {
              select.empty()
              for (let item in data) {
                for (let i in data[item]) {
                  select.append(_$('<option>').attr('value', i).text(data[item][i]))
                }
              }
              setTimeout(function () {
                _$('select[name="tipo_model"]').val(formData.tipo_model)
              }, 200)
              // select.change(onChangeParamTA)
            })
          })

          /* modalDs.find('input[name="num_ta"], '
            +'input[name="ano_ta"], '
            +'select[name="tipo_model"], '
            +'input[name="texto_dispositivo"], '
            +'input[name="dispositivos_internos"], '
            +'input[name="rotulo_dispositivo"]'
          ).change(onChangeParamTA); */
          modalDs.find('input[name="texto_dispositivo"], ' +
              'input[name="rotulo_dispositivo"]')
            .on('keyup', onKeyPressRotuloBuscaTextual)

          modalDs.find('.btn-busca').click(onChangeParamTA)

          modalDs.find('#btn-modal-select').click(function () {
            // limpar selecionados se o tipo é radio
            let listas = field.find('ul')
            if (dataTypeSelection === 'radio') {
              listas.remove()
            }
            // adicionar itens selecionados na caixa modal
            let selecionados = modalDs.find('[name="' + dataField + '"]:checked')

            // com base nos selecionados, limpa seus ta's removendo os não selecionados
            selecionados.closest('ul').find('input:not(:checked)').filter('[name!="ta_select_all"]').closest('li').remove()

            selecionados.closest('ul').each(function () {
              // insere na lista de selecionados os ta's não presentes
              let ulLista = field.find('#' + this.id)
              if (ulLista.length === 0) {
                field.append(this)
                return
              }

              // insere os dispositivos não presentes
              let inputForThis = _$(this).find('input')

              inputForThis.each(function () {
                if (ulLista.find('#' + this.id).length > 0) {
                  return
                }
                ulLista.append(_$(this).closest('li'))
              })
            })

            onChangeFieldSelects()

            modalDs.modal('hide')

            if ('post_selected' in opts) {
              opts['post_selected'](opts['params_post_selected'])
            }
          })

          try {
            formData = JSON.parse(window.localStorage.getItem('dispositivo_search_form_data'))
            _$('input[name="num_ta"]').val(formData.num_ta)
            _$('input[name="ano_ta"]').val(formData.ano_ta)
            _$('input[name="rotulo_dispositivo"]').val(formData.rotulo)
            _$('input[name="texto_dispositivo"]').val(formData.texto)
            _$('select[name="max_results"]').val(formData.max_results)
          } catch (e) {
            // console.log(e)
          }

          setTimeout(function () {
            try {
              _$('select[name="tipo_ta"]').val(formData.tipo_ta)
              _$('select[name="tipo_ta"]').trigger('change')
              // modalDs.find('.btn-busca').trigger('click')
              // onChangeParamTA()
            } catch (e) {
              // console.log(e)
            }
          }, 200)

          modalDs.modal('show')
        })
      })
    })
  })
}

export default {
  SetCookie,
  ReadCookie,
  insertWaitAjax,
  DispositivoSearch
}
