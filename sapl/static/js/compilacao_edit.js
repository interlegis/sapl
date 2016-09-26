function DispositivoEdit() {
    // Função única - Singleton pattern - operador new sempre devolve o mesmo objeto
    var instance;

    var editortype = "textarea";

    if (!(this instanceof DispositivoEdit)) {
        if (!instance) {
            instance = new DispositivoEdit();
        }
        return instance;
    }
    instance = this;
    DispositivoEdit = function() {
        return instance;
    };

    instance.bindActionsEditorType = function(event) {
        editortype = this.getAttribute('editortype');
        SetCookie("editortype", editortype, 30);
        var dpt = $(this).closest('.dpt');

        var pk = dpt.attr('pk');
        instance.clearEditSelected();
        instance.triggerBtnDptEdit(pk);
    }

    instance.bindActionsClick = function(event) {
        var pk = this.getAttribute('pk');

        var form_data = {
            'action'    : this.getAttribute('action'),
            'tipo_pk'   : this.getAttribute('tipo_pk'),
            'perfil_pk' : this.getAttribute('perfil_pk'),
            'variacao'  : this.getAttribute('variacao'),
        };

        var url = pk+'/refresh';
        instance.waitShow();

        $.get(url, form_data).done(function(data) {
            instance.clearEditSelected();
            if (data.pk != null) {
                if (data.message !== undefined) {
                    if (data.message.modal) {
                        instance.modalMessage(data.message.value, 'alert-'+data.message.type, function() {
                            instance.waitShow();
                            instance.refreshScreenFocusPk(data);
                        });
                        return;
                    }
                    else {
                        instance.message(data)
                    }
                }
                instance.refreshScreenFocusPk(data);
            }
        }).fail(instance.waitHide).always(instance.waitHide);
    }

    instance.clearEditSelected = function() {
        $('.dpt-selected > .dpt-form').html('');
        $('.dpt-actions, .dpt-actions-bottom').html('');
        tinymce.remove();
        $('.dpt-selected').removeClass('dpt-selected');
    }

    instance.editDispositivo = function(event) {
        var obj_click = (event.target.classList.contains('dpt-link')
                            ? event.target
                            : (event.target.parentElement.classList.contains('dpt-link')
                                ? event.target.parentElement
                                : null));

        if (obj_click && obj_click.getAttribute('href') && obj_click.getAttribute('href').length > 0)
            return;

        var dpt = $(this).closest('.dpt');
        if (dpt.hasClass('dpt-selected')) {
            if (this.getAttribute('action') == 'editor-close')
                instance.clearEditSelected();
            return;
        }
        instance.clearEditSelected();
        instance.loadActionsEdit(dpt);

        var formtype = dpt.attr('formtype');
        dpt.on(formtype, instance[formtype]);
        instance.loadForm(dpt, formtype);
    }

    instance.gc = function() {
        setTimeout(function() {
            $('.dpt:not(.dpt-selected) > .dpt-form').html('');
        },500);
    }

    instance.get_form_base = function () {
        var _this = $(this);
        _this.addClass('dpt-selected');

        var dpt_form = _this.children().filter('.dpt-form');
        dpt_form.find('form').submit(instance.onSubmitEditFormBase);

        instance.scrollTo(_this);
        _this.off('get_form_base')

        var btn_fechar = _this.find('.btn-fechar');
        btn_fechar.on('click', function() {
            instance.clearEditSelected();
        });

        var btns_excluir = _this.find('.btns-excluir');
        _this.find('.dpt-actions-bottom').first().append(btns_excluir);

        btns_excluir.find('.btn-excluir').on('click', instance.bindActionsClick);
    }

    instance.get_form_alteracao = function () {
        var _this = $(this);
        _this.off('get_form_alteracao');
        $('.dpt-actions, .dpt-actions-bottom').html('');

        var dpt_form = _this.children().filter('.dpt-form').children().first();
        var url_search = dpt_form[0]['id_dispositivo_search_form'].value;
        DispostivoSearch({
          'url_form': url_search,
          'text_button': 'Selecionar'
        });

        instance.scrollTo(_this);
        dpt_form.submit(instance.onSubmitFormRegistraAlteracao);

        var btn_fechar = _this.find('.btn-fechar');
        btn_fechar.on('click', function() {
            instance.clearEditSelected();
            instance.triggerBtnDptEdit(_this.attr('pk'));
        });
    }

    instance.get_form_inclusao = function () {
        var _this = $(this);
        _this.off('get_form_inclusao');
        $('.dpt-actions, .dpt-actions-bottom').html('');

        var dpt_form = _this.children().filter('.dpt-form').children().first();
        var url_search = dpt_form[0]['id_dispositivo_search_form'].value;
        DispostivoSearch({
          'url_form': url_search,
          'text_button': 'Selecionar',
          'post_selected': instance.update_radio_allowed_inserts
        });

        instance.scrollTo(_this);
        dpt_form.submit(instance.onSubmitFormRegistraInclusao);

        var btn_fechar = _this.find('.btn-fechar');
        btn_fechar.on('click', function() {
            instance.clearEditSelected();
            instance.triggerBtnDptEdit(_this.attr('pk'));
        });
    }

    instance.get_form_revogacao = function () {
        var _this = $(this);
        _this.off('get_form_revogacao');
        $('.dpt-actions, .dpt-actions-bottom').html('');

        var dpt_form = _this.children().filter('.dpt-form').children().first();
        var url_search = dpt_form[0]['id_dispositivo_search_form'].value;
        DispostivoSearch({
          'url_form': url_search,
          'text_button': 'Selecionar'
        });

        instance.scrollTo(_this);
        dpt_form.submit(instance.onSubmitFormRegistraRevogacao);

        var btn_fechar = _this.find('.btn-fechar');
        btn_fechar.on('click', function() {
            instance.clearEditSelected();
            instance.triggerBtnDptEdit(_this.attr('pk'));
        });
    }

    instance.update_radio_allowed_inserts = function(event) {

        dispositivo_base_para_inclusao = $("input[name='dispositivo_base_para_inclusao']")
        if (dispositivo_base_para_inclusao.length == 0)
            return
        var pk = dispositivo_base_para_inclusao[0].value;

        var form_data = {
            'action'    : 'get_form_radio_allowed_inserts'
        };

        var url = pk+'/refresh';
        instance.waitShow();

        $.get(url, form_data).done(function(data) {
            $(".allowed_inserts").html(data);
        }).fail(instance.waitHide).always(instance.waitHide);

    }

    instance.loadActionsEdit = function(dpt) {
        var pk = dpt.attr('pk');
        var url = pk+'/refresh?action=get_actions';
        $.get(url).done(function(data) {
            dpt.find('.dpt-actions').first().html(data);
            dpt.find('.btn-action').on('click', instance.bindActionsClick);
            //dpt.find('.btn-perfis').on('click', instance.bindActionsClick);
            dpt.find('.btn-compila').on('click', instance.loadFormsCompilacao);
            dpt.find('.btn-editor-type').on('click', instance.bindActionsEditorType);

            if (editortype == 'construct')
                dpt.find('.btn-group-inserts').first().addClass('open');

            dpt.find('.btn-group-inserts button').mouseenter(function(event) {
                dpt.find('.btn-group-inserts').removeClass('open');
                $(this.parentElement).addClass('open')
            });

            instance.gc();
        });
    }

    instance.loadForm = function(dpt, trigger) {
        var pk = dpt.attr('pk');
        var dpt_form = dpt.children().filter('.dpt-form');
        if (dpt_form.length == 1) {
            var url = pk+'/refresh?action='+trigger;
            $.get(url).done(function(data) {
                if (editortype != "construct") {
                    dpt_form.html(data);
                    if (editortype == 'tinymce' ) {
                        initTinymce();
                    }
                }
                dpt.trigger(trigger);
            }).always(function() {
                instance.waitHide();
            });
        }
    }

    instance.loadFormsCompilacao = function(event) {
        var dpt = $(this).closest('.dpt');
        var formtype = this.getAttribute('action');
        dpt.on(formtype, instance[formtype]);
        instance.loadForm(dpt, formtype);
    }

    instance.modalMessage = function(message, alert, closeFunction) {
        if (message != null && message != '') {
            $('#modal-message #message').html(message);
            $('#modal-message').modal('show');
            $('#modal-message, #modal-message .alert button').off();
            $('#modal-message .alert').removeClass('alert-success alert-info alert-warning alert-danger alert-danger');
            $('#modal-message .alert').addClass(alert);

            if (closeFunction != null)
                $('#modal-message').on('hidden.bs.modal', closeFunction);

            $('#modal-message .alert button').on('click', function() {
                $('#modal-message').modal('hide');
            });
            return true;
        }
        return false;
    }

    instance.message = function(data) {
        if (!('message' in data))
            return;
        var cp_notify = $(".cp-notify")
        cp_notify.removeClass('hide')
        var msg = cp_notify.find('.message');
        msg.text(data.message.value);
        msg.removeClass('bg-primary bg-success bg-info bg-warning bg-danger').addClass('bg-'+data.message.type);
        setTimeout(function() {
            cp_notify.addClass('hide');
        }, (data.message.time?data.message.time: 3000));
    }
    instance.offClicks = function() {
        $('.btn-dpt-edit').off()
    }
    instance.onClicks = function(container) {
        var objects;
        if (container == null)
            objects = $('.btn-dpt-edit');
        else
            objects = $(container).find('.btn-dpt-edit');
        objects.on('click', instance.editDispositivo);
    }

    instance.onSubmitFormRegistraAlteracao = function(event) {
        var _this = this;

        var form_data = {
            'csrfmiddlewaretoken'  : this['csrfmiddlewaretoken'].value,
            'dispositivo_alterado' : this['dispositivo_alterado'].value,
            'formtype': 'get_form_alteracao',
        };
        var url = $(this).closest('.dpt').attr( "pk" )+'/refresh';

        instance.waitShow();

        $.post(url, form_data)
        .done(function(data) {
            instance.clearEditSelected();

            if (data.pk != null) {
                instance.refreshScreenFocusPk(data);
                instance.message(data);
            }
            else {
                alert('Erro na resposta!');
            }

        }).always(function() {
            instance.waitHide();
        });
        if (event != null)
            event.preventDefault();
    }

    instance.onSubmitFormRegistraInclusao = function(event) {
        var _this = this;

        var form_data = {
            'csrfmiddlewaretoken'  : this['csrfmiddlewaretoken'].value,
            'dispositivo_base_para_inclusao' : this['dispositivo_base_para_inclusao'].value,
            'formtype': 'get_form_inclusao',
        };
        var url = $(this).closest('.dpt').attr( "pk" )+'/refresh';

        instance.waitShow();

        $.post(url, form_data)
        .done(function(data) {
            instance.clearEditSelected();

            if (data.pk != null) {
                instance.refreshScreenFocusPk(data);
                instance.message(data);
            }
            else {
                alert('Erro na resposta!');
            }

        }).always(function() {
            instance.waitHide();
        });
        if (event != null)
            event.preventDefault();
    }

    instance.onSubmitFormRegistraRevogacao = function(event) {
        var _this = this;

        var form_data = {
            'csrfmiddlewaretoken'  : this['csrfmiddlewaretoken'].value,
            'dispositivo_revogado' : this['dispositivo_revogado'].value,
            'formtype': 'get_form_revogacao',
        };
        var url = $(this).closest('.dpt').attr( "pk" )+'/refresh';

        instance.waitShow();

        $.post(url, form_data)
        .done(function(data) {
            instance.clearEditSelected();

            if (data.pk != null) {
                instance.refreshScreenFocusPk(data);
                instance.message(data);
            }
            else {
                alert('Erro na resposta!');
            }

        }).always(function() {
            instance.waitHide();
        });
        if (event != null)
            event.preventDefault();
    }

    instance.onSubmitEditFormBase = function(event) {

        var _this = this;
        var texto = '';
        var texto_atualizador = '';
        var visibilidade = '';
        var editor_tiny_texto = tinymce.get('id_texto');
        var editor_tiny_texto_atualizador = tinymce.get('id_texto_atualizador');

        if (editor_tiny_texto != null)
            texto = editor_tiny_texto.getContent();
        else
            texto = this['id_texto'].value;

        if (editor_tiny_texto_atualizador != null)
            texto_atualizador = editor_tiny_texto_atualizador.getContent();
        else if ('id_texto_atualizador' in this)
            texto_atualizador = this['id_texto_atualizador'].value;

        if ('visibilidade' in this)
            visibilidade = this['visibilidade'].value;

        var form_data = {
            'csrfmiddlewaretoken' : this['csrfmiddlewaretoken'].value,
            'texto'               : texto,
            'texto_atualizador'   : texto_atualizador,
            'visibilidade'        : visibilidade,
            'formtype': 'get_form_base',
        };

        var url = $(this).closest('.dpt').attr( "pk" )+'/refresh';

        instance.waitShow();

        $.post(url, form_data)
        .done(function(data) {
            if (typeof data == "string") { /* if obsoleto */
                var dpt = $(_this).closest('.dpt');
                dpt = $('#'+dpt.replaceWith(data).attr('id'));
                instance.onClicks(dpt);
                instance.waitHide();
                return;
            }
            instance.clearEditSelected();

            if (data.pk != null) {
                instance.refreshScreenFocusPk(data);
                instance.message(data);
            }
            else {
                alert('Erro na resposta!');
            }

        }).always(function() {
            instance.waitHide();
        });
        if (event != null)
            event.preventDefault();
    }
    instance.refreshContent = function(pais, trigger_edit_pk) {
        if (pais.length == 0) {
            instance.waitHide();
            return;
        }
        var pk = pais.shift();
        var url = pk+'/refresh';

        $.get(url).done(function(data) {
            var dpt = $('#id'+pk).closest('.dpt');
            dpt = $('#'+dpt.replaceWith(data).attr('id'));
            instance.onClicks(dpt);
            instance.reloadFunctionsDraggables();

            if (trigger_edit_pk > 0)
                instance.triggerBtnDptEdit(trigger_edit_pk)

            instance.refreshContent(pais);
        });
    }
    instance.refreshScreenFocusPk = function (data) {
        instance.waitShow();
        if (data.pai[0] == -1) {
            instance.waitShow()
            href = location.href.split('#')[0]
            location.href = href+'#'+data.pk;
            location.reload(true)
            }
        else {
            instance.refreshContent(data.pai, data.pk);

            /*setTimeout(function() {
                for (var pai = 1; pai < data.pai.length; pai++)
                    instance.refreshContent(data.pai[pai]);
                instance.waitHide();
            }, 1000);*/
        }
    }

    instance.reloadFunctionsDraggables = function() {
        $( ".dpt-alts" ).sortable({
          revert: true,
          distance: 15,
          start: function( event, ui ) {
          }
          ,
          stop: function( event, ui ) {
              var pk = ui.item.attr('pk');
              var bloco_pk = ui.item.closest('.dpt-alts').closest('.dpt').attr('pk');

              var url = pk+'/refresh?action=json_drag_move_dpt_alterado&index='+ui.item.index()+'&bloco_pk='+bloco_pk;
              $.get(url).done(function( data ) {
                  console.log(pk+ ' - '+ bloco_pk);
                  //reloadFunctionsForObjectsOfCompilacao();
              });
          }
        });

        $( ".dpt-alts .dpt" ).draggable({
          connectToSortable: ".dpt-alts",
          revert: 'invalid',
          zIndex: 1,
          distance: 15,
          drag: function( event, ui ) {
              //$('.dpt-comp-selected').removeClass('dpt-comp-selected');
              $(".dpt-alts").addClass('drag');
          },
          stop: function( event, ui ) {
              $(".dpt-alts").removeClass('drag');
          },
        });

        $(".dpt-alts").disableSelection();
    }
    instance.scrollTo = function(dpt) {
        try {
            $('html, body').animate({
                scrollTop: dpt.offset().top - window.innerHeight / 9
            }, 100);
        }
        catch(err) {
        }
    }
    instance.triggerBtnDptEdit =function(pk)  {
        var btn_dpt_edit = $('#id'+pk + ' > .dpt-text.btn-dpt-edit');
        if (btn_dpt_edit.length == 0)
            btn_dpt_edit = $('#id'+pk + ' > .dpt-actions-fixed > .btn-dpt-edit');
        btn_dpt_edit.trigger( "click" );
    }
    instance.waitHide = function() {
         $("#wait_message").addClass("displaynone");
    }
    instance.waitShow = function() {
         $("#wait_message").removeClass("displaynone");
    }


    instance.init = function() {
        editortype = ReadCookie("editortype");
        if (editortype == null || editortype == '') {
            editortype = "textarea"
            SetCookie("editortype", editortype, 30)
        }
        //editortype = "textarea";
        instance.offClicks();
        instance.onClicks();
        instance.reloadFunctionsDraggables();

        href = location.href.split('#')
        if (href.length == 2 && href[1] != '') {
            instance.triggerBtnDptEdit(href[1])
        }
        $('main').click(function(event) {
            if (event.target == this || event.target == this.firstElementChild)
                instance.clearEditSelected();
        });
        instance.waitHide();
    }
    instance.init();
}


$(document).ready(function() {

    DispositivoEdit();

});
