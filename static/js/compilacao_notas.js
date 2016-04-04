
function onEventsDneExec(pk, model) {

    $('html, body').animate({
        scrollTop: $('#dne' + pk ).offset().top - window.innerHeight / 5
    }, 300);

    refreshDatePicker();

    $('#dne'+pk+" #button-id-submit-form").click(onSubmitEditNVForm);
    $('#dne'+pk+" .btn-close-container").click(function(){
        $(this).closest('.dne-nota').removeClass('dne-nota');
        $(this).closest('.dne-form').html('');
    });

    if (model == 'nota') {
        $('#dne'+pk+" select[name='tipo']").change(function(event) {
            var url = '';
            url = 'text/'+pk+'/nota/create?action=modelo_nota&id_tipo='+this.value;
            $.get(url).done(function( data ) {
                $('#dne'+pk+" textarea[name='texto']").val(data);
            });
        });
    }
    else if (model == 'vide') {
        configFormSearchTA('#dne'+pk, 'radio', 'select_for_vide');

        onChangeParamTA();
    }
}


var onSubmitEditNVForm = function(event) {

    var url = '';
    var model = 'nota';
    var id_edit = null;
    var id_dispositivo = $('#id_dispositivo').val();

    if (id_dispositivo == null) { // trata-se de um vide
        $('#id_dispositivo_ref').remove();
        id_dispositivo = $('#id_dispositivo_base').val();
        model='vide';
    }

    id_edit = $('#id_pk').val();
    url = 'text/'+id_dispositivo+'/'+model+'/'
    if (id_edit == null || id_edit == '')
        url += 'create';
    else
        url += id_edit+'/edit';

    console.log($('#dne'+id_dispositivo+" form").serialize());

    $.post( url, $('#dne'+id_dispositivo+" form").serialize(), function(data) {

            if (typeof data == "string") {
                if (data.indexOf('<form') >= 0) {
                    $('#dne'+id_dispositivo+' .dne-form').html(data);
                    onEventsDneExec(id_dispositivo, model);
                }
                else {
                    $('#dne'+id_dispositivo+' .dne-form').closest('.dpt').html(data)
                    onReadyNotasVides();
                    try {
                        $('html, body').animate({
                        scrollTop: $('#dne' + id_dispositivo ).offset().top - window.innerHeight / 3
                        }, 300);
                    }
                    catch(err) {
                    }
                }
            }
        }
    );
}
var onDelete = function(event) {

    var model = $(event).attr('model');

    var id_dispositivo =  $(event).closest('.dn').attr('pk');
    var id_delete = $(event).attr('pk');
    var url = 'text/'+id_dispositivo+'/'+model+'/'+id_delete+'/delete';

    $.get( url, function(data) {
        $('#dne'+id_dispositivo+' .dne-form').closest('.dpt').html(data)
        onReadyNotasVides();
        }
    );
}

function getForm(_this) {

    var url = '';
    var model = $(_this).attr('model');
    var id_dispositivo = $('.dne-nota .dne-form').closest('.dne').attr('pk');
    if (id_dispositivo != null) {
        $('#dne'+id_dispositivo).removeClass('dne-nota');
        $('#dne'+id_dispositivo+' .dne-form').html('');
    }

    if (_this.className.indexOf('create') >= 0 ) {
        id_dispositivo = $(_this).attr('pk');
        url = 'text/'+id_dispositivo+'/'+model+'/create';
    }
    else if (_this.className.indexOf('edit') >= 0 ) {
        var id_edit = $(_this).attr('pk');
        id_dispositivo = $(_this).closest('.dn').attr('pk');
        url = 'text/'+id_dispositivo+'/'+model+'/'+id_edit+'/edit'
    }

    $('#dne'+id_dispositivo).addClass('dne-nota');

    $.get(url).done(function( data ) {
        $('#dne'+id_dispositivo+' .dne-form').html(data);
        onEventsDneExec(id_dispositivo, model);
    }).fail(function() {
        onReadyNotasVides();
    });
}

function onReadyNotasVides() {

        $('.dne-nota').removeClass('dne-nota');
        $('.dne-form').html('');

        $('.dne .btn-action').off();
        $('.dn .btn-action').off();

        $('.dne .btn-action, .dn .btn-action').not('.btn-nota-delete').not('.btn-vide-delete').click(function(){
            getForm(this);
        });

        $('.dn .btn-nota-delete, .dn .btn-vide-delete').click(function(){
            onDelete(this);
        });
}
$(document).ready(function() {
    onReadyNotasVides()
});
