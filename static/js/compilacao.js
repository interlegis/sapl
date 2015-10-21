
$(document).ready(function() {

var flag_add_next = false
var flag_add_next_pk = 0
var flag_add_next_pai = 0

var withTinymce = false

var onSubmitEditForm = function(event) {

    var texto = ''
    var editorTiny = tinymce.get('editdi_texto')

    if (editorTiny != null)
       texto = editorTiny.getContent();
    else
       texto = $('#editdi_texto').val();

    var formData = {
        'csrfmiddlewaretoken' : $('input[name=csrfmiddlewaretoken]').val(),
        'texto'               : texto
    };
    var url = $('.editdi_form form').attr( "action_ajax" );
    $("#message_block").css("display", "block");
    $.post(url,formData)
        .done(function(data) {
            $('.editselected').html(data);
            clearEditSelected();
            reloadFunctionClicks();
        }).always(function() {
            $("#message_block").css("display", "none");
        }); 
    event.preventDefault(); 
}

var clickEditDispositivo = function(event) { 
    var _pk = event.currentTarget.getAttribute('pk');
    if ($('#de'+_pk).hasClass("editselected")) {
        clearEditSelected();
        return;
    }
    clearEditSelected();
    clickUpdateDispositivo(event)
}

var clickUpdateDispositivo = function(event, __pk, __action, addeditselected) {

    var _pk = __pk;
    var _action = __action;
    var _variacao = '';
    var _tipo_pk = '';

    if (event != null) {
        _pk = event.currentTarget.getAttribute('pk');
        _action = $(this).attr('action');
        _variacao = $(this).attr('variacao');
        _tipo_pk = $(this).attr('tipo_pk');
    }

    if (flag_add_next_pk == 0)
        flag_add_next_pk = _pk

    var url = ''
    if (_action == '')
        return
    else if ( _action == null || _action.startsWith('refresh')) {

        if (_action != null && _action.endsWith('tinymce'))
           withTinymce = true;
        else if (_action != null && _action.endsWith('textarea'))
           withTinymce = false;

        url = _pk+'/refresh?pkadd='+flag_add_next_pk+url;

        }
    else {
        url = _pk+'/actions?action='+_action;
        url += '&tipo_pk='+_tipo_pk;
        url += '&variacao='+_variacao;
        if (addeditselected == null || addeditselected) {
            $("#message_block").css("display", "block");
        }
    }

    $.get(url).done(function( data ) {

        if ( _action == null || _action.startsWith('refresh')) {
        
            if (flag_add_next) {
            
                if (addeditselected)
                    clearEditSelected();
                    
                $( '#de' + _pk ).html( data);
                flag_add_next = false
            } 
            else {
                clearEditSelected();
                $( '#de' + _pk ).prepend( data );
            }
            reloadFunctionClicks();

            if ( withTinymce ) { 
                initTinymce()
            }
            else { 
            	$('.editdi_form form').submit(onSubmitEditForm);
            }

            if (addeditselected == null || addeditselected) {
                $('#de'+flag_add_next_pk).addClass('editselected');
                $('html, body').animate({
                    scrollTop: $('#de' + flag_add_next_pk ).offset().top - window.innerHeight / 10 
                    }, 300);
                flag_add_next_pk = 0;
            }
        }

        else if (_action == 'add_next') {

            clearEditSelected();

            flag_add_next_pk = data.pk;
            flag_add_next_pai = data.pai;
            
            if (flag_add_next_pk != null)
                for (var pai = 0; pai < flag_add_next_pai.length; pai++)
                     if (flag_add_next_pai[pai] != -1) {
                          flag_add_next = true;
                          flag_add_next_pk = data.pk;
                          clickUpdateDispositivo(null, flag_add_next_pai[pai], 'refresh', pai == 0);
                     }
                     else {
                         href = location.href.split('#')[0]
                         location.href = href+'#'+flag_add_next_pk
                         location.reload(true)
                     }
            else {
                alert('Erro na inserção!');
                flag_add_next_pk = 0;
                flag_add_next = false;
                }
        }
    }).always(function() {
        $("#message_block").css("display", "none");
    });
}


function clearEditSelected() {
    tinymce.remove();
    $('.editselected').removeClass('editselected');
    $('.editdi_form').remove();
    $('.editselected .label_pai, .edit .label_pai').remove();
    $('.editselected .actions_head, .edit .actions_head').remove();
    $('.editselected .actions_footer, .edit .actions_footer').remove();
}

function reloadFunctionClicks() { 
    $('.dispositivo .edit .di').off();
    $('.actions .btn-action').off();
    $('.actions_head .btn-action').off();
    $('.dispositivo .edit .di').on('click', clickEditDispositivo);
    $('.actions .btn-action').on('click', clickEditDispositivo);
    $('.actions_head .btn-action').on('click', clickUpdateDispositivo);
}

function initTinymce() {

	tinymce.init({ 
        mode : "textareas", 
        force_br_newlines : false,
        force_p_newlines : false,
        forced_root_block : '',
        plugins: ["table save code"],
        menubar: "edit format table tools",
        toolbar: "save | undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",
        tools: "inserttable",  
        save_onsavecallback: onSubmitEditForm,
        border_css: "/static/styles/compilacao_tinymce.css",
        content_css: "/static/styles/compilacao_tinymce.css"
    });
}


reloadFunctionClicks();
$("#message_block").css("display", "none");

});

