
let _$ = window.$

window.DispositivoEdit = function () {
  // Função única - Singleton pattern - operador new sempre devolve o mesmo objeto
  let instance

  let editortype = 'textarea'

  if (!(this instanceof window.DispositivoEdit)) {
    if (!instance) {
      instance = new window.DispositivoEdit()
    }
    return instance
  }
  instance = this
  window.DispositivoEdit = function () {
    return instance
  }

  instance.bindActionsEditorType = function (event) {
    editortype = this.getAttribute('editortype')
    window.SetCookie('editortype', editortype, 30)
    let dpt = _$(this).closest('.dpt')

    let pk = dpt.attr('pk')
    instance.clearEditSelected()
    instance.triggerBtnDptEdit(pk)
    event.preventDefault()
  }

  instance.bindActionsClick = function (event) {
    let pk = this.getAttribute('pk')

    let form_data = {
      'action': this.getAttribute('action'),
      'tipo_pk': this.getAttribute('tipo_pk'),
      'perfil_pk': this.getAttribute('perfil_pk'),
      'variacao': this.getAttribute('variacao'),
      'pk_bloco': this.getAttribute('pk_bloco')
    }

    let url = pk + '/refresh'
    instance.waitShow()

    _$.get(url, form_data).done(function (data) {
      instance.clearEditSelected()
      if (data.pk != null) {
        instance.message(data)
      }
    }).fail(instance.waitHide).always(instance.waitHide)
  }

  instance.clearEditSelected = function () {
    _$('.dpt-selected > .dpt-form').html('')
    _$('.dpt-actions, .dpt-actions-bottom').html('')
    window.tinymce.remove()
    _$('.dpt-selected').removeClass('dpt-selected')
  }

  instance.editDispositivo = function (event) {
    let obj_click = (event.target.classList.contains('dpt-link')
      ? event.target
      : (event.target.parentElement.classList.contains('dpt-link')
        ? event.target.parentElement
        : null))

    if (obj_click && obj_click.getAttribute('href') && obj_click.getAttribute('href').length > 0) { return }

    let dpt = _$(this).closest('.dpt')
    if (dpt.hasClass('dpt-selected')) {
      if (this.getAttribute('action') === 'editor-close') { instance.clearEditSelected() }
      return
    }
    instance.clearEditSelected()
    instance.loadActionsEdit(dpt)

    let formtype = dpt.attr('formtype')
    dpt.on(formtype, instance[formtype])
    instance.loadForm(dpt, formtype)
  }

  instance.gc = function () {
    setTimeout(function () {
      _$('.dpt:not(.dpt-selected) > .dpt-form').html('')
    }, 500)
  }

  instance.get_form_base = function () {
    let _this = _$(this)
    _this.addClass('dpt-selected')

    let dpt_form = _this.children().filter('.dpt-form')
    dpt_form.find('form').submit(instance.onSubmitEditFormBase)

    instance.scrollTo(_this)
    _this.off('get_form_base')

    let btn_fechar = _this.find('.btn-fechar')
    btn_fechar.on('click', function (event) {
      instance.clearEditSelected()
      event.preventDefault()
    })

    let btns_excluir = _this.find('.btns-excluir')
    _this.find('.dpt-actions-bottom').first().append(btns_excluir)

    btns_excluir.find('.btn-outline-danger').on('click', instance.bindActionsClick)
  }

  instance.get_form_alteracao = function () {
    let _this = _$(this)
    _this.off('get_form_alteracao')
    _$('.dpt-actions, .dpt-actions-bottom').html('')

    let dpt_form = _this.children().filter('.dpt-form').children().first()
    let url_search = dpt_form[0]['id_dispositivo_search_form'].value
    window.DispositivoSearch({
      'url_form': url_search,
      'text_button': 'Selecionar'
    })

    instance.scrollTo(_this)
    dpt_form.submit(instance.onSubmitFormRegistraAlteracao)

    let btn_fechar = _this.find('.btn-fechar')
    btn_fechar.on('click', function (event) {
      instance.clearEditSelected()
      instance.triggerBtnDptEdit(_this.attr('pk'))
      event.preventDefault()
    })
  }

  instance.get_form_inclusao = function () {
    let _this = _$(this)
    _this.off('get_form_inclusao')
    _$('.dpt-actions, .dpt-actions-bottom').html('')

    let dpt_form = _this.children().filter('.dpt-form').children().first()
    let url_search = dpt_form[0]['id_dispositivo_search_form'].value
    window.DispositivoSearch({
      'url_form': url_search,
      'text_button': 'Selecionar',
      'post_selected': instance.allowed_inserts_registro_inclusao,
      'params_post_selected': { 'pk_bloco': _this.attr('pk') }

    })

    instance.scrollTo(_this)
    dpt_form.submit(instance.onSubmitFormRegistraInclusao)

    let btn_fechar = _this.find('.btn-fechar')
    btn_fechar.on('click', function (event) {
      instance.clearEditSelected()
      instance.triggerBtnDptEdit(_this.attr('pk'))
      event.preventDefault()
    })
  }

  instance.get_form_revogacao = function () {
    let _this = _$(this)
    _this.off('get_form_revogacao')
    _$('.dpt-actions, .dpt-actions-bottom').html('')

    let dpt_form = _this.children().filter('.dpt-form').children().first()
    let url_search = dpt_form[0]['id_dispositivo_search_form'].value
    window.DispositivoSearch({
      'url_form': url_search,
      'text_button': 'Selecionar'
    })

    instance.scrollTo(_this)
    dpt_form.submit(instance.onSubmitFormRegistraRevogacao)

    let btn_fechar = _this.find('.btn-fechar')
    btn_fechar.on('click', function () {
      instance.clearEditSelected()
      instance.triggerBtnDptEdit(_this.attr('pk'))
    })
  }

  instance.allowed_inserts_registro_inclusao = function (params) {
    let dispositivo_base_para_inclusao = _$('#id' + params.pk_bloco + " input[name='dispositivo_base_para_inclusao']")
    if (dispositivo_base_para_inclusao.length === 0) { return }

    let pk = dispositivo_base_para_inclusao[0].value
    let form_data = {
      'action': 'get_actions_allowed_inserts_registro_inclusao',
      'pk_bloco': params.pk_bloco
    }

    let url = pk + '/refresh'
    instance.waitShow()

    _$.get(url, form_data).done(function (data) {
      _$('.allowed_inserts').html(data)
      _$('.allowed_inserts').find('.btn-action').on('click', instance.bindActionsClick)
    }).fail(instance.waitHide).always(instance.waitHide)
  }

  instance.loadActionsEdit = function (dpt) {
    let pk = dpt.attr('pk')
    let url = pk + '/refresh?action=get_actions'
    _$.get(url).done(function (data) {
      dpt.find('.dpt-actions').first().html(data)
      dpt.find('.btn-action').on('click', instance.bindActionsClick)
      // dpt.find('.btn-perfis').on('click', instance.bindActionsClick);
      dpt.find('.btn-compila').on('click', instance.loadFormsCompilacao)
      dpt.find('.btn-editor-type').on('click', instance.bindActionsEditorType)

      if (editortype === 'construct') { dpt.find('.btn-group-inserts').first().addClass('open') }

      dpt.find('.btn-group-inserts button').mouseenter(function (event) {
        dpt.find('.btn-group-inserts').removeClass('open')
        _$(this.parentElement).addClass('open')
      })

      instance.gc()
    })
  }

  instance.loadForm = function (dpt, trigger) {
    let pk = dpt.attr('pk')
    let dpt_form = dpt.children().filter('.dpt-form')
    if (dpt_form.length === 1) {
      let url = pk + '/refresh?action=' + trigger
      _$.get(url).done(function (data) {
        if (editortype !== 'construct') {
          dpt_form.html(data)
          if (editortype === 'tinymce') {
            window.initTextRichEditor()
          }
          // OptionalCustomFrontEnd().init()
        }
        dpt.trigger(trigger)
      }).always(function () {
        instance.waitHide()
      })
    }
  }

  instance.loadFormsCompilacao = function (event) {
    let dpt = _$(this).closest('.dpt')
    let formtype = this.getAttribute('action')
    dpt.on(formtype, instance[formtype])
    instance.loadForm(dpt, formtype)
  }

  instance.modalMessage = function (message, alert, closeFunction) {
    if (message !== null && message !== '') {
      _$('#modal-message #message').html(message)
      _$('#modal-message').modal('show')
      _$('#modal-message, #modal-message .alert button').off()
      _$('#modal-message .alert').removeClass('alert-success alert-info alert-warning alert-danger alert-danger')
      _$('#modal-message .alert').addClass(alert)

      if (closeFunction != null) { _$('#modal-message').on('hidden.bs.modal', closeFunction) }

      _$('#modal-message .alert button').on('click', function () {
        _$('#modal-message').modal('hide')
      })
      return true
    }
    return false
  }

  instance.message = function (data) {
    if (data.message !== undefined) {
      if (data.message.modal) {
        instance.modalMessage(data.message.value, 'alert-' + data.message.type, function () {
          instance.waitShow()
          instance.refreshScreenFocusPk(data)
        })
      } else {
        instance.refreshScreenFocusPk(data)
        if (!('message' in data)) { return }
        let cp_notify = _$('.cp-notify')
        cp_notify.removeClass('hide')
        let msg = cp_notify.find('.message')
        msg.text(data.message.value)
        msg.removeClass('bg-primary bg-success bg-info bg-warning bg-danger').addClass('bg-' + data.message.type)
        setTimeout(function () {
          cp_notify.addClass('hide')
        }, (data.message.time ? data.message.time : 3000))
      }
    } else {
      instance.refreshScreenFocusPk(data)
    }
  }
  instance.offClicks = function () {
    _$('.btn-dpt-edit').off()
  }
  instance.onClicks = function (container) {
    let objects
    if (container == null) { objects = _$('.btn-dpt-edit') } else { objects = _$(container).find('.btn-dpt-edit') }
    objects.on('click', instance.editDispositivo)
  }

  instance.onSubmitFormRegistraAlteracao = function (event) {
    if (this.dispositivo_alterado === undefined) {
      instance.modalMessage('Nenhum dispositivo selecionado', 'alert-info')
      if (event != null) { event.preventDefault() }
      return
    }
    let dispositivo_alterado = this.dispositivo_alterado.length === undefined ? [ this.dispositivo_alterado ] : Array.from(this.dispositivo_alterado)
    let form_data = {
      'csrfmiddlewaretoken': this.csrfmiddlewaretoken.value,
      'dispositivo_alterado': dispositivo_alterado.filter(
        function (elem, idx, array) {
          return elem.checked
        }
      ).map(function (dsp) {
        return dsp.value
      }),
      'formtype': 'get_form_alteracao'
    }
    let url = _$(this).closest('.dpt').attr('pk') + '/refresh'

    instance.waitShow()

    // eslint-disable-next-line
    _$.post(url, form_data)
      .done(function (data) {
        instance.clearEditSelected()

        if (data.pk != null) {
          instance.message(data)
        } else {
          alert('Erro na resposta!')
        }
      }).always(function () {
        instance.waitHide()
      })
    if (event != null) { event.preventDefault() }
  }

  instance.onSubmitFormRegistraInclusao = function (event) {
    let form_data = {
      'csrfmiddlewaretoken': this['csrfmiddlewaretoken'].value,
      'dispositivo_base_para_inclusao': this['dispositivo_base_para_inclusao'].value,
      'formtype': 'get_form_inclusao'
    }
    let url = _$(this).closest('.dpt').attr('pk') + '/refresh'

    instance.waitShow()

    _$.post(url, form_data)
      .done(function (data) {
        instance.clearEditSelected()

        if (data.pk != null) {
          instance.message(data)
        } else {
          alert('Erro na resposta!')
        }
      }).always(function () {
        instance.waitHide()
      })
    if (event != null) { event.preventDefault() }
  }

  instance.onSubmitFormRegistraRevogacao = function (event) {
    if (this.dispositivo_revogado === undefined) {
      instance.modalMessage('Nenhum dispositivo selecionado', 'alert-info')
      if (event != null) { event.preventDefault() }
      return
    }
    let dispositivo_revogado = this.dispositivo_revogado.length === undefined ? [ this.dispositivo_revogado ] : Array.from(this.dispositivo_revogado)
    let form_data = {
      'csrfmiddlewaretoken': this.csrfmiddlewaretoken.value,
      'dispositivo_revogado': dispositivo_revogado.filter(
        function (elem, idx, array) {
          return elem.checked
        }
      ).map(function (dsp) {
        return dsp.value
      }),
      'revogacao_em_bloco': this.revogacao_em_bloco.value,
      'formtype': 'get_form_revogacao'
    }

    let url = _$(this).closest('.dpt').attr('pk') + '/refresh'

    instance.waitShow()

    _$.post(url, form_data)
      .done(function (data) {
        instance.clearEditSelected()

        if (data.pk != null) {
          instance.message(data)
        } else {
          alert('Erro na resposta!')
        }
      }).always(function () {
        instance.waitHide()
      })
    if (event != null) { event.preventDefault() }
  }

  instance.onSubmitEditFormBase = function (event) {
    let _this = this
    let texto = ''
    let texto_atualizador = ''
    let visibilidade = ''
    let editor_tiny_texto = window.tinymce.get('id_texto')
    let editor_tiny_texto_atualizador = window.tinymce.get('id_texto_atualizador')

    if (editor_tiny_texto != null) { texto = editor_tiny_texto.getContent() } else { texto = this['id_texto'].value }

    if (editor_tiny_texto_atualizador != null) { texto_atualizador = editor_tiny_texto_atualizador.getContent() } else if ('id_texto_atualizador' in this) { texto_atualizador = this['id_texto_atualizador'].value }

    if ('visibilidade' in this) { visibilidade = this['visibilidade'].value }

    let form_data = {
      'csrfmiddlewaretoken': this['csrfmiddlewaretoken'].value,
      'texto': texto,
      'texto_atualizador': texto_atualizador,
      'visibilidade': visibilidade,
      'formtype': 'get_form_base'
    }

    let url = _$(this).closest('.dpt').attr('pk') + '/refresh'

    instance.waitShow()

    _$.post(url, form_data)
      .done(function (data) {
        if (typeof data === 'string') { /* if obsoleto */
          let dpt = _$(_this).closest('.dpt')
          dpt = _$('#' + dpt.replaceWith(data).attr('id'))
          instance.onClicks(dpt)
          instance.waitHide()
          return
        }
        instance.clearEditSelected()

        if (data.pk != null) {
          instance.message(data)
        } else {
          alert('Erro na resposta!')
        }
      }).always(function () {
        instance.waitHide()
      })
    if (event != null) { event.preventDefault() }
  }
  instance.refreshContent = function (pais, trigger_edit_pk) {
    if (pais.length === 0) {
      instance.waitHide()
      return
    }
    let pk = pais.shift()
    let url = pk + '/refresh'

    _$.get(url).done(function (data) {
      let dpt = _$('#id' + pk).closest('.dpt')
      dpt = _$('#' + dpt.replaceWith(data).attr('id'))
      instance.onClicks(dpt)
      instance.reloadFunctionsDraggables()

      if (trigger_edit_pk > 0) { instance.triggerBtnDptEdit(trigger_edit_pk) }

      instance.refreshContent(pais)
    })
  }
  instance.refreshScreenFocusPk = function (data) {
    instance.waitShow()
    if (data.pai[0] === -1) {
      instance.waitShow()
      let href = location.href.split('#')[0]
      location.href = href + '#' + data.pk
      location.reload(true)
    } else {
      instance.refreshContent(data.pai, data.pk)

      /* setTimeout(function() {
                for (let pai = 1; pai < data.pai.length; pai++)
                    instance.refreshContent(data.pai[pai]);
                instance.waitHide();
            }, 1000); */
    }
  }

  instance.reloadFunctionsDraggables = function () {
    _$('.dpt-alts').sortable({
      revert: true,
      distance: 15,
      start: function (event, ui) {
      },
      stop: function (event, ui) {
        let pk = ui.item.attr('pk')
        let bloco_pk = ui.item.closest('.dpt-alts').closest('.dpt').attr('pk')

        let url = pk + '/refresh?action=json_drag_move_dpt_alterado&index=' + ui.item.index() + '&bloco_pk=' + bloco_pk
        _$.get(url).done(function (data) {
          console.log(pk + ' - ' + bloco_pk)
          // reloadFunctionsForObjectsOfCompilacao();
        })
      }
    })

    _$('.dpt-alts .dpt').draggable({
      connectToSortable: '.dpt-alts',
      revert: 'invalid',
      zIndex: 1,
      distance: 15,
      drag: function (event, ui) {
        // _$('.dpt-comp-selected').removeClass('dpt-comp-selected');
        _$('.dpt-alts').addClass('drag')
      },
      stop: function (event, ui) {
        _$('.dpt-alts').removeClass('drag')
      }
    })

    _$('.dpt-alts').disableSelection()
  }
  instance.scrollTo = function (dpt) {
    try {
      _$('html, body').animate({
        scrollTop: dpt.offset().top - window.innerHeight / 9
      }, 100)
    } catch (err) {
    }
  }
  instance.triggerBtnDptEdit = function (pk) {
    let btn_dpt_edit = _$('#id' + pk + ' > .dpt-text.btn-dpt-edit')
    if (btn_dpt_edit.length === 0) { btn_dpt_edit = _$('#id' + pk + ' > .dpt-actions-fixed > .btn-dpt-edit') }
    btn_dpt_edit.trigger('click')
  }
  instance.waitHide = function () {
    _$('#wait_message').addClass('displaynone')
  }
  instance.waitShow = function () {
    _$('#wait_message').removeClass('displaynone')
  }

  instance.init = function () {
    _$('.dpt-actions-fixed').first().css('opacity', '1')
    editortype = window.ReadCookie('editortype')
    if (editortype === null || editortype === '') {
      editortype = 'textarea'
      window.SetCookie('editortype', editortype, 30)
    }
    // editortype = "textarea";
    instance.offClicks()
    instance.onClicks()
    instance.reloadFunctionsDraggables()

    let href = location.href.split('#')
    if (href.length === 2 && href[1] !== '') {
      instance.triggerBtnDptEdit(href[1])
    }
    _$('main').click(function (event) {
      if (event.target === this || event.target === this.firstElementChild) { instance.clearEditSelected() }
    })
    instance.waitHide()
  }
  instance.init()
}

_$(document).ready(function () {
  window.DispositivoEdit()
})
