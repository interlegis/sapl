
var flag_add_next = false;
var flag_add_next_pk = 0;
var flag_add_next_pai = 0;

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
    $.post(url,formData)
        .done(function(data) {
            $('.dpt-selected').html(data);
            clearEditSelected();
            reloadFunctionClicks();
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
    else if ( _action == null)
        url = _pk+'/refresh?pkadd='+flag_add_next_pk;
    else if (_action.startsWith('refresh')) {

        var str = _action.split(':');
        if (str.length > 1) {
            editortype = str[1];
        }

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

                $( '#dpt' + _pk ).html( data);
                flag_add_next = false
            }
            else {
                clearEditSelected();
                $( '#dpt' + _pk ).prepend( data );
            }
            reloadFunctionClicks();
 
            if ( editortype == 'tinymce' ) {
                initTinymce();
            }
            else if (editortype == 'textarea') {
            	$('.csform form').submit(onSubmitEditForm);
            }
            else if (editortype == 'construct') {
                $('.csform .btn-salvar').parent().remove();
                $('.csform .btn-salvar, .csform textarea').remove();
                $('#dpt'+flag_add_next_pk).css('min-height', $('.actions_right').height()*2);
                $('.actions_inserts').removeClass('menu_flutuante');
            }
            $(".edt-"+editortype).addClass('selected');
            //$(".container").addClass('class_color_container');

            if (addeditselected == null || addeditselected) {
                $('html, body').animate({
                    scrollTop: $('#dpt' + flag_add_next_pk ).offset().top - window.innerHeight / 10
                    }, 300);
                $('#dpt'+flag_add_next_pk).addClass('dpt-selected');
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
        else {
            clearEditSelected();
            reloadFunctionClicks();
            flag_add_next_pk = 0;
        }
    }).always(function() {
        $("#message_block").css("display", "none");
    });
}


function clearEditSelected() {
    $(".container").removeClass('class_color_container');
    tinymce.remove();
    $('.dpt-selected').removeClass('dpt-selected');
    $('.dpt').css('min-height', '');
    $('.csform').remove();
}

function reloadFunctionClicks() {
    $('.dpt .de, .btn-action, .btn-inserts, .btn-edit').off();

    $('.dpt .de, .btn-edit').on('click', clickEditDispositivo);

    $('.btn-action, .btn-inserts').on(
			'click', clickUpdateDispositivo);


    $('#editdi_texto').focus();
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


$(document).ready(function() {

	reloadFunctionClicks();
	$("#message_block").css("display", "none");

	 clickUpdateDispositivo(null, 60933, 'refresh', true);

});
