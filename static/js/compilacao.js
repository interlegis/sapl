
var editortype = "textarea";
var gets = 0;
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

	if (event != null) {
		pk_refresh = event.currentTarget.getAttribute('pk');
		_action = $(this).attr('action');
		_variacao = $(this).attr('variacao');
		_tipo_pk = $(this).attr('tipo_pk');
	}

	if (pk_edit == null)
		pk_edit = pk_refresh;

	var url = '';
	if (_action == '')
		return;
	else if ( _action == null) {
		url = pk_refresh+'/refresh?pkadd='+pk_edit;
	}
	else if (_action.startsWith('refresh')) {

		var str = _action.split(':');
		if (str.length > 1) {
			editortype = str[1];
			SetCookie("editortype", editortype, 30)

		}
		url = pk_refresh+'/refresh?pkadd='+pk_edit+url;
				$("#message_block").css("display", "block");
	}
	else {

		url = pk_refresh+'/actions?action='+_action;
		url += '&tipo_pk='+_tipo_pk;
		url += '&variacao='+_variacao;

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
			else if (_editortype == 'detail') {
				$('.csform .btn-salvar').parent().removeClass("displaynone");
				$('.csform .btn-salvar,  .csform .fields').removeClass("displaynone");
				$('#dpt'+pk_refresh).css('min-height', $('.actions_right').height()*2);
				$('.actions_inserts').addClass('menu_flutuante');
			}

			$(".edt-"+_editortype).addClass('selected');
			//$(".container").addClass('class_color_container');

			if (flag_actions_vibible == null || flag_actions_vibible) {
				$('html, body').animate({
					scrollTop: $('#dpt' + pk_edit ).offset().top - window.innerHeight / 10
				}, 300);
				$('#dpt'+pk_edit).addClass('dpt-selected');
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
		else {
			clearEditSelected();
			reloadFunctionClicks();
		}
	}).always(function() {
		$("#message_block").css("display", "none");
	});
}

function refreshScreenFocusPk(data) {

	for (var pai = 0; pai < data.pai.length; pai++)
		if (data.pai[pai] != -1) {
			clickUpdateDispositivo(null, data.pai[pai], data.pk, 'refresh', pai == 0, true);
		}
		else {
			href = location.href.split('#')[0]
			location.href = href+'#'+data.pk
			location.reload(true)
		}
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

	$('.btn-action, .btn-inserts').on('click', clickUpdateDispositivo);

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

//cookies
function SetCookie(cookieName,cookieValue,nDays) {
	var today = new Date();
	var expire = new Date();
	if (nDays==null || nDays==0) nDays=1;
	expire.setTime(today.getTime() + 3600000*24*nDays);
	document.cookie = cookieName+"="+escape(cookieValue)
	+ ";expires="+expire.toGMTString();
}

function ReadCookie(cookieName) {
	var theCookie=" "+document.cookie;
	var ind=theCookie.indexOf(" "+cookieName+"=");
	if (ind==-1) ind=theCookie.indexOf(";"+cookieName+"=");
	if (ind==-1 || cookieName=="") return "";
	var ind1=theCookie.indexOf(";",ind+1);
	if (ind1==-1) ind1=theCookie.length;
	return unescape(theCookie.substring(ind+cookieName.length+2,ind1));
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
	if (href.length == 2) {
		clickUpdateDispositivo(null, href[1], href[1], 'refresh', true);
	}

});
