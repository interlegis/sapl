const _$ = window.$

function SetCookie (cookieName, cookieValue, nDays) {
  const today = new Date()
  const expire = new Date()
  if (nDays === null || nDays === 0) nDays = 1
  expire.setTime(today.getTime() + 3600000 * 24 * nDays)
  document.cookie = cookieName + '=' + escape(cookieValue) +
    ';expires=' + expire.toGMTString()
}

function ReadCookie (cookieName) {
  const theCookie = ' ' + document.cookie
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

    const fields = _$('[data-sapl-ta="DispositivoSearch"]')
    fields.each(function () {
      const field = _$(this)
      const dataTypeSelection = field.attr('data-type-selection')
      const dataField = field.attr('data-field')
      const dataFunction = field.attr('data-function')

      const onChangeFieldSelects = function (event) {
        if (dataTypeSelection === 'checkbox') {
          const tas = field.find('input[name="ta_select_all"]') // tas - Textos Articulados
          tas.off()

          tas.on('change', function (event) {
            _$(this).closest('ul').find('input[name="' + dataField + '"]').prop('checked', this.checked)
            // _$(this).prop('checked', false)
          })
        } else {
          const dpts = field.find('input')
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

      const onChangeParamTA = function (event) {
        const tipoTa = _$('select[name="tipo_ta"]').val()
        const tipoModel = _$('select[name="tipo_model"]').val()
        const numTa = _$('input[name="num_ta"]').val()
        const anoTa = _$('input[name="ano_ta"]').val()
        let tipoResultado = _$('input[name="tipo_resultado"]:checked').val()
        const rotuloDispositivo = _$('input[name="rotulo_dispositivo"]').val()
        const textoDispositivo = _$('input[name="texto_dispositivo"]').val()
        const maxResults = _$('select[name="max_results"]').val()
        let url = ''

        if (rotuloDispositivo.length > 0 || textoDispositivo.length > 0) {
          _$('input[name="tipo_resultado"]').prop('disabled', false)
          _$('input[name="tipo_resultado"]').each((idx, element) => {
            element.parentElement.classList.remove('disabled')
          })
          _$('input[name="tipo_resultado"]').closest('#div_id_tipo_resultado').css('opacity', '1')
        } else {
          _$('input[name="tipo_resultado"]').filter('[value="False"]').prop('checked', true)
          _$('input[name="tipo_resultado"]').prop('disabled', true)

          _$('input[name="tipo_resultado"]').each((idx, element) => {
            element.parentElement.classList.add('disabled')
          })
          _$('input[name="tipo_resultado"]').closest('#div_id_tipo_resultado').css('opacity', '0.3')
          tipoResultado = 'False'
        }
        formData = {
          tipo_ta: tipoTa,
          tipo_model: tipoModel,
          num_ta: numTa,
          ano_ta: anoTa,
          texto: textoDispositivo,
          rotulo: rotuloDispositivo,
          tipo_resultado: tipoResultado,
          max_results: maxResults,
          data_type_selection: dataTypeSelection,
          data_field: dataField,
          data_function: dataFunction
        }

        window.localStorage.setItem('dispositivo_search_form_data', JSON.stringify(formData))

        url = '/ta/search_fragment_form'
        _$('.result-busca-dispositivo').html('')
        insertWaitAjax('.result-busca-dispositivo')
        _$.get(url, formData).done(function (data) {
          _$('.result-busca-dispositivo').html(data)
          // OptionalCustomFrontEnd().init()
          if (dataTypeSelection === 'checkbox') {
            const tas = _$('.result-busca-dispositivo').find('input[name="ta_select_all"]')
            tas.off()
            tas.on('change', function (event) {
              _$(this).closest('ul').find('input[name="' + dataField + '"]').prop('checked', this.checked)
            })
          }
        })
      }

      const onKeyPressRotuloBuscaTextual = function (event) {
        const rotuloDispositivo = _$('input[name="rotulo_dispositivo"]').val()
        const textoDispositivo = _$('input[name="texto_dispositivo"]').val()
        // let tipoResultado = _$('input[name="tipo_resultado"]:checked').val()

        if (rotuloDispositivo.length > 0 || textoDispositivo.length > 0) {
          _$('input[name="tipo_resultado"]').prop('disabled', false)
          _$('input[name="tipo_resultado"]').each((idx, element) => {
            element.parentElement.classList.remove('disabled')
          })
          _$('input[name="tipo_resultado"]').closest('#div_id_tipo_resultado').css('opacity', '1')
        } else {
          _$('input[name="tipo_resultado"]').filter('[value="False"]').prop('checked', true)
          _$('input[name="tipo_resultado"]').prop('disabled', true)
          _$('input[name="tipo_resultado"]').each((idx, element) => {
            element.parentElement.classList.add('disabled')
          })
          _$('input[name="tipo_resultado"]').closest('#div_id_tipo_resultado').css('opacity', '0.3')
          // tipoResultado = 'False'
        }
      }

      let buttonDs = field.children('#buttonDs')
      if (buttonDs.length > 0) {
        _$(buttonDs).remove()
      }
      buttonDs = _$('<div id="buttonDs" class="clearfix"/>')
      field.prepend(buttonDs)

      const btnOpenSearch = _$('<button>')
        .text(opts.text_button)
        .attr('type', 'button')
        .attr('class', 'btn btn-sm btn-success btn-modal-open')
      buttonDs.append(btnOpenSearch)
      btnOpenSearch.on('click', function () {
        _$.get(opts.url_form, function (data) {
          containerDs.html(data)
          const modalDs = _$('#modal-ds')
          // OptionalCustomFrontEnd().init()

          modalDs.find('select[name="tipo_ta"]').change(function (event) {
            let url = ''
            url = '/ta/search_fragment_form?action=get_tipos&tipo_ta=' + this.value
            modalDs.find('label[for="id_tipo_model"]').html('Tipos de ' + this.children[this.selectedIndex].innerHTML)

            const select = modalDs.find('select[name="tipo_model"]')
            select.empty()
            _$('<option value="">Carregando...</option>').appendTo(select)

            _$.get(url).done(function (data) {
              select.empty()
              for (const item in data) {
                for (const i in data[item]) {
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
            +'input[name="tipo_resultado"], '
            +'input[name="rotulo_dispositivo"]'
          ).change(onChangeParamTA); */
          modalDs.find('input[name="texto_dispositivo"], ' +
              'input[name="rotulo_dispositivo"]')
            .on('keyup', onKeyPressRotuloBuscaTextual)

          modalDs.find('.btn-busca').click(onChangeParamTA)

          modalDs.find('#btn-modal-select').click(function () {
            // limpar selecionados se o tipo é radio
            const listas = field.find('ul')
            if (dataTypeSelection === 'radio') {
              listas.remove()
            }
            // adicionar itens selecionados na caixa modal
            const selecionados = modalDs.find('[name="' + dataField + '"]:checked')

            // com base nos selecionados, limpa seus ta's removendo os não selecionados
            selecionados.closest('ul').find('input:not(:checked)').filter('[name!="ta_select_all"]').closest('li').remove()

            selecionados.closest('ul').each(function () {
              // insere na lista de selecionados os ta's não presentes
              const ulLista = field.find('#' + this.id)
              if (ulLista.length === 0) {
                field.append(this)
                return
              }

              // insere os dispositivos não presentes
              const inputForThis = _$(this).find('input')

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
              opts.post_selected(opts.params_post_selected)
            }
          })

          try {
            formData = JSON.parse(window.localStorage.getItem('dispositivo_search_form_data'))
            _$('input[name="num_ta"]').val(formData.num_ta)
            _$('input[name="ano_ta"]').val(formData.ano_ta)
            _$('input[name="rotulo_dispositivo"]').val(formData.rotulo)
            _$('input[name="texto_dispositivo"]').val(formData.texto)
            _$('select[name="max_results"]').val(formData.max_results)

            _$('input[name="tipo_resultado"]')
              .filter(`[value="${formData.tipo_resultado}"]`)
              .attr('checked', true)
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
      if ('autostart' in opts && opts.autostart) {
        btnOpenSearch.trigger('click')
      }
    })
  })
}

function InitViewTAs () {
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
        // console.log(err)
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

  $('.cp-linha-vigencias > li:not(:first-child):not(:last-child) > a').click(function (event) {
    $('.cp-linha-vigencias > li').removeClass('active')
    $(this).closest('li').addClass('active')
    event.preventDefault()
  })

  $('main').click(function (event) {
    if (event.target === this || event.target === this.firstElementChild) {
      $('.cp-linha-vigencias > li').removeClass('active')
    }
  })
}

export default {
  SetCookie,
  ReadCookie,
  insertWaitAjax,
  InitViewTAs,
  DispositivoSearch
}
