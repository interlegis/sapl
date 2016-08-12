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

    instance.clearEditSelected = function() {
        $('.dpt-selected .dpt-form').html('');
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
            instance.clearEditSelected();
            return;
        }
        instance.clearEditSelected();

        dpt.on('get_form_base', function () {
            var _this = $(this);
            _this.addClass('dpt-selected');
            var pk = _this.attr('pk');
            instance.scrollTo(_this);
            _this.off('get_form_base')

            var btn_fechar = _this.find('.btn-fechar');
            btn_fechar.on('click', function() {
                instance.clearEditSelected();
            });

            var btns_excluir = _this.find('.btns-excluir');
            _this.find('.dpt-actions-bottom').last().append(btns_excluir);

            btns_excluir.find('.btn-excluir').on('click', function() {
                var action = this.getAttribute('action');

                if (pk !== undefined) {
                    var url = pk+'/refresh?action='+action;
                    instance.waitShow();
                    $.get(url).done(function(data) {
                        instance.clearEditSelected();
                        instance.waitHide();
                        if (data.pk != null) {
                            if (instance.modalMessage(data.message.value, 'alert-'+data.message.type, function() {
                                    //instance.waitHide();
                                }))
                            instance.refreshScreenFocusPk(data);
                        }
                    });
                }
            });
            instance.loadActionsProvaveisInserts(pk)

        });
        instance.loadForm(dpt, 'get_form_base');
    }

    instance.loadActionsProvaveisInserts = function(pk) {
        var url = pk+'/refresh?action=json_provaveis_inserts';
        instance.waitShow();
        $.get(url).done(function(data) {
            console.log(data);
        });
    }

    instance.loadForm = function(dpt, trigger) {
        if (editortype == "construct")
            return;
        var dpt_form = dpt.children().filter('.dpt-form');
        if (dpt_form.length == 1) {
            var pk = dpt.attr('pk');
            var url = pk+'/refresh?action='+trigger;
            $.get(url).done(function(data) {
                dpt_form.html(data);
                dpt_form.find('form').submit(instance.onSubmitEditFormBase);
                if (editortype == 'tinymce' ) {
                    initTinymce();
                }
                dpt.trigger(trigger);
            }).always(function() {
                instance.waitHide();
            });
        }
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
            'visibilidade'        : visibilidade
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
        editortype = "textarea";
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
