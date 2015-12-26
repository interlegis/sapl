
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

	$('#dne'+pk+" .primary").click(onSubmitEditForm);
	$('#dne'+pk+" .btn-close-container").click(function(){
		$(this).closest('.dne-nota').removeClass('dne-nota');
		$(this).closest('.dne-form').html('');
	});

	$('#dne'+pk+" select[name='tipo']").change(function(event) {
		var url = '';
		url = 'text/'+pk+'/nota/create?action=modelo_nota&id_tipo='+this.value;
		$.get(url).done(function( data ) {
			$('#dne'+pk+" textarea[name='texto']").val(data);
		});
	});

	$('#dne'+pk+" select[name='tipo_norma']"
	).change(onChangeParamNorma);

	$('#dne'+pk+" input[name='num_norma'], "
		+ '#dne'+pk+" input[name='ano_norma'], "
		+ '#dne'+pk+" input[name='busca_dispositivo']"
	).change(onChangeParamNorma);

	$('#dne'+pk+" .btn-busca").click(onChangeParamNorma);

	onChangeParamNorma();
}
var onChangeParamNorma = function(event) {
	var tipo_ta = $("select[name='tipo_ta']").val();
	var num_ta = $("input[name='num_ta']").val();
	var ano_ta = $("input[name='ano_ta']").val();
	var busca_dispositivo = $("input[name='busca_dispositivo']").val();
	var dispositivo_ref = $("#id_dispositivo_ref").val();
	$('#id_dispositivo_ref').remove();

	if (dispositivo_ref == null)
		dispositivo_ref = ''

	var url = '';
	var pk = $("select[name='tipo_ta']").closest('.dne').attr('pk')

	var formData = {
		'tipo_ta'            : tipo_ta,
		'num_ta'             : num_ta,
		'ano_ta'             : ano_ta,
		'busca'               	: busca_dispositivo,
		'tipo_form'             : 'radio',
		'initial_ref'           : dispositivo_ref
	};

	url = 'text/search';
	$('.container-busca').html('');
	insertWaitAjax('.container-busca')
	$.get(url, formData).done(function( data ) {
		$('.container-busca').html(data);
		$("input[name='dispositivo_ref']").first().prop('checked', true);
	});
}

var onSubmitEditForm = function(event) {

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
					onEventsDneExec(id_dispositivo);
				}
				else {
					$('#dne'+id_dispositivo+' .dne-form').closest('.dpt').html(data)
					onReadyNotasVides();

					$('html, body').animate({
						scrollTop: $('#dne' + id_dispositivo ).offset().top - window.innerHeight / 3
					}, 300);

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
		onEventsDneExec(id_dispositivo);
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
