
function onEventsDneExec(pk) {

	$('html, body').animate({
		scrollTop: $('#dne' + pk ).offset().top - window.innerHeight / 5
	}, 300);

	$('.dateinput').fdatepicker({
        // TODO localize
        format: 'dd/mm/yyyy',
        language: 'pt',
        endDate: '31/12/2100',
        todayBtn: true
    });

	$('#dne'+pk+" select[name='tipo']").change(function(event) {
		var url = '';
		url = 'compilacao/'+pk+'/nota/create?action=modelo_nota&id_tipo='+this.value;
		$.get(url).done(function( data ) {
			$('#dne'+pk+" textarea[name='texto']").val(data);
		});
	});

	$('#dne'+pk+" .button").click(onSubmitEditForm);
}

var onSubmitEditForm = function(event) {

	var id_dispositivo = $('#id_dispositivo').val();
	var id_nota = $('#id_pk').val();
	var url = 'compilacao/'+id_dispositivo+'/nota/'

	if (id_nota == '')
		url += 'create';
	else
		url += id_nota+'/edit';

	$.post( url, $('#dne'+id_dispositivo+" form").serialize(), function(data) {

			if (typeof data == "string") {
				if (data.indexOf('<form') >= 0) {
					$('#dne'+id_dispositivo+' .dne-form').html(data);
					onEventsDneExec(id_dispositivo);
				}
				else {
					$('#dne'+id_dispositivo+' .dne-form').closest('.dpt').html(data)
					onReadyNotas();
				}
			}
		}
	);
}
var onDelete = function(event) {

	var id_dispositivo =  $(event).closest('.dn').attr('pk');
	var id_nota = $(event).attr('pk');
	var url = 'compilacao/'+id_dispositivo+'/nota/'+id_nota+'/delete'

	$.get( url, function(data) {
		$('#dne'+id_dispositivo+' .dne-form').closest('.dpt').html(data)
		onReadyNotas();
		}
	);
}
function getFormNota(_this, _btn) {

	var id_dispositivo = $('.dne-exec .dne-form').closest('.dne').attr('pk');
	if (id_dispositivo != null) {
		$('#dne'+id_dispositivo).removeClass('dne-exec');
		$('#dne'+id_dispositivo+' .dne-form').html('');
	}

	var url = '';
	if (_btn == 'btn-create') {
		id_dispositivo = $(_this).attr('pk');
		url = 'compilacao/'+id_dispositivo+'/nota/create';
		}
	else if (_btn == 'btn-edit') {
		var id_nota = $(_this).attr('pk');
		id_dispositivo = $(_this).closest('.dn').attr('pk');
		url = 'compilacao/'+id_dispositivo+'/nota/'+id_nota+'/edit'
	}
	$('#dne'+id_dispositivo).addClass('dne-exec');

	$.get(url).done(function( data ) {
		$('#dne'+id_dispositivo+' .dne-form').html(data);
		onEventsDneExec(id_dispositivo);
	});
}
function onReadyNotas() {
		$('.dne .btn-create').off();
		$('.dne .btn-edit').off();
		$('.dne .btn-delete').off();
		$('.dne .btn-create').click(function(){
			getFormNota(this, 'btn-create')
		});
		$('.dn .btn-edit').click(function(){
			getFormNota(this, 'btn-edit')
		});
		$('.dn .btn-delete').click(function(){
			onDelete(this, 'btn-delete')
		});
}
$(document).ready(function() {
	onReadyNotas()
});
