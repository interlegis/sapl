
var editortype = "textarea";
var onSubmitEditForm = function(event) {

    var texto = '';
    var editorTiny = tinymce.get('editdi_texto');

    if (editorTiny != null)
        texto = editorTiny.getContent();
    else
        texto = $('#editdi_texto').val();

    var formData = {
        'csrfmiddlewaretoken' : $('input[name=csrfmiddlewaretoken]').val(),
        'texto'               : texto
    };

    var url = $('.csform form').attr( "action_ajax" );
    $("#message_block").css("display", "block");

    $.post(url, formData)
    .done(function(data) {

        if (typeof data == "string") {
            $('.dpt-selected').html(data);
            clearEditSelected();
            reloadFunctionClicks();
            return;
        }

        clearEditSelected();

        if (data.pk != null)
            refreshScreenFocusPk(data);
        else {
            alert('Erro na inserção!');
            flag_refresh_all = false;
        }

    }).always(function() {
        $("#message_block").css("display", "none");
    });
    if (event != null)
        event.preventDefault();
}


var clickEditDispositivo = function(event) {
    var _pk = event.currentTarget.getAttribute('pk');
    if ($('#dpt'+_pk).hasClass("dpt-selected")) {
        clearEditSelected();
        return;
    }
    clearEditSelected();
    clickUpdateDispositivo(event);
}

var clickUpdateDispositivo = function(event, __pk_refresh, __pk_edit, __action, flag_actions_vibible, flag_refresh_all) {

    var pk_refresh = __pk_refresh;
    var pk_edit = __pk_edit;
    var _action = __action;
    var _variacao = '';
    var _tipo_pk = '';
    var _perfil_pk = '';

    if (event != null) {
        pk_refresh = event.currentTarget.getAttribute('pk');
        _action = $(this).attr('action');
        _variacao = $(this).attr('variacao');
        _tipo_pk = $(this).attr('tipo_pk');
        _perfil_pk = $(this).attr('perfil_pk');
    }

    if (pk_edit == null)
        pk_edit = pk_refresh;

    var url = '';
    if (_action == '')
        return;
    else if ( _action == null) {
        url = pk_refresh+'/refresh?edit='+pk_edit;
    }
    else if (_action.startsWith('refresh')) {
        var str = _action.split(':');
        if (str.length > 1) {
            if(_action.endsWith('perfil')) {
                url = '&perfil_pk='+_perfil_pk;
                $("#message_block").css("display", "block");
            }
            else {
                editortype = str[1];
                SetCookie("editortype", editortype, 30)
            }
        }
        url = pk_refresh+'/refresh?edit='+pk_edit+url;
    }
    else if (_action.startsWith('add_')) {

        url = pk_refresh+'/actions?action='+_action;
        url += '&tipo_pk='+_tipo_pk;
        url += '&variacao='+_variacao;

        $("#message_block").css("display", "block");

    }
    else if (_action.startsWith('set_')) {

        url = pk_refresh+'/actions?action='+_action;
        $("#message_block").css("display", "block");

    }
    else if (_action.startsWith('delete_')) {
        var r = confirm("Confirma Exclusão deste dispositivo?");
        if (!r) {
            return
        }
        url = pk_refresh+'/actions?action='+_action;
        $("#message_block").css("display", "block");
    }

    $.get(url).done(function( data ) {
        if ( _action == null || _action.startsWith('refresh')) {

            if (flag_refresh_all) {
                if (flag_actions_vibible)
                    clearEditSelected();

                $( '#dpt' + pk_refresh ).html( data);
            }
            else {
                //console.log(pk_refresh + ' - '+pk_edit)
                if (flag_actions_vibible == null || flag_actions_vibible)
                    clearEditSelected();

                //$( '#dpt' + pk_refresh+' > .bloco' ).addClass('displaynone' );
                $( '#dpt' + pk_refresh ).prepend( data );
            }

            reloadFunctionClicks();

            var _editortype = editortype;
            if ( $('.edt-'+_editortype).length == 0) {
                _editortype = 'construct';
            }

            if ( _editortype == 'tinymce' ) {
                initTinymce();
            }
            else if (_editortype == 'textarea') {
                $('.csform form').submit(onSubmitEditForm);
            }
            else if (_editortype == 'construct') {
                $('.csform .btn-salvar').parent().addClass("displaynone");
                $('.csform .btn-salvar, .csform .fields').addClass("displaynone");
                $('#dpt'+pk_refresh).css('min-height', $('.actions_right').height()*2);
                $('.actions_inserts').removeClass('menu_flutuante');
            }
            else if (_editortype == 'detail') { //TODO: código obsoleto - confirmar retirada desta condição
                $('.csform .btn-salvar').parent().removeClass("displaynone");
                $('.csform .btn-salvar,  .csform .fields').removeClass("displaynone");
                $('#dpt'+pk_refresh).css('min-height', $('.actions_right').height()*2);
                $('.actions_inserts').addClass('menu_flutuante');
            }

            $(".edt-"+_editortype).addClass('selected');

            if (flag_actions_vibible == null || flag_actions_vibible) {
                $('#dpt'+pk_edit).addClass('dpt-selected');
                try {
                    $('html, body').animate({
                        scrollTop: $('#dpt' + pk_edit ).offset().top - window.innerHeight / 9
                    }, 100);
                }
                catch(err) {
                }
            }
        }

        else if (_action == 'add_next' || _action == 'add_in') {
            clearEditSelected();
            if (data.pk != null) {
                refreshScreenFocusPk(data);
            }
            else {
                alert('Erro na inserção!');
            }
        }
        else if (_action.startsWith('delete_')) {
            $("#message_block").css("display", "block");
            clearEditSelected();
            if (data.pk != null) {
                if (!modalMessage(data.message, 'alert-danger', function() {
                        //refreshScreenFocusPk(data);
                    }))
                    refreshScreenFocusPk(data);
            }
            else {
                alert('Erro exclusão de Dispositivo!');
            }
        }
        else {
            clearEditSelected();
            reloadFunctionClicks();
            modalMessage(data.message, 'alert-success', null);
        }

    }).always(function() {
        $("#message_block").css("display", "none");
    });
}

function modalMessage(message, alert, closeFunction) {
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

function refreshScreenFocusPk(data) {

    if (data.pai[0] == -1) {
        $("#message_block").css("display", "block");
        href = location.href.split('#')[0]
        location.href = href+'#'+data.pk;
        location.reload(true)
        }
    else {
        clickUpdateDispositivo(null, data.pai[0], data.pk, 'refresh', true, true);
        setTimeout(function() {
            for (var pai = 1; pai < data.pai.length; pai++)
                clickUpdateDispositivo(null, data.pai[pai], data.pk, 'refresh', false, true);
        }, 1000);
    }
}

function clearEditSelected() {
    $('.bloco' ).removeClass('displaynone' );

    $(".container").removeClass('class_color_container');
    tinymce.remove();
    $('.dpt-selected').removeClass('dpt-selected');
    $('.dpt').css('min-height', '');
    $('.csform').remove();
}

function reloadFunctionClicks() {
    $('.dpt .de, .btn-action, .btn-edit').off();

    $('.dpt .de, .btn-edit').on('click', clickEditDispositivo);

    $('.btn-action').on('click', clickUpdateDispositivo);

    $('#editdi_texto').focus();
    $( ".bloco_alteracao" ).sortable({
      revert: true,
      stop: function( event, ui ) {
          var pk = ui.item.attr('pk');
          var pk_bloco = ui.item.closest('.bloco').closest('.dpt').attr('pk');
          console.log(pk+ ' - '+ pk_bloco);
      },
    });

    $( ".bloco_alteracao .dpt" ).draggable({
      connectToSortable: ".bloco_alteracao",
      revert: 'invalid',
      zIndex: 1,
      drag: function( event, ui ) {
          $( ".bloco_alteracao" ).css('border-width', '2px');
      },
      stop: function( event, ui ) {
          $( ".bloco_alteracao" ).css('border-width', '0px');
      },
    });

    $( ".bloco_alteracao" ).disableSelection();
}

$(document).ready(function() {

    editortype = ReadCookie("editortype")

    if (editortype == null || editortype == "") {
        editortype = "textarea"
        SetCookie("editortype", editortype, 30)
    }

    reloadFunctionClicks();
    $("#message_block").css("display", "none");

    href = location.href.split('#')
    if (href.length == 2 && href[1] != '') {
        clickUpdateDispositivo(null, href[1], href[1], 'refresh', true);
    }

    $('main').click(function(event) {
        if (event.target == this || event.target == this.firstElementChild)
            clearEditSelected();
    });

});
