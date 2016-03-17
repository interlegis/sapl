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

function insertWaitAjax(element) {
    //jQuery(element).append('<div style="text-align:center;"><img src="/static/img/ajax-loader.gif"></div>');
    jQuery(element).append('<div style="text-align:center;"><i style="font-size: 200%;"class="fa fa-refresh fa-spin"></i></div>');
}


var tipo_select = '';
var tipo_form = '';
var configFormSearchTA = function(container, _tipo_form, _tipo_select) {
	tipo_select = _tipo_select;
	tipo_form = _tipo_form;
    var ta_select = $(container+" select[name='tipo_ta']");
    $(container+" label[for='id_tipo_model']").html('Tipos de ' + ta_select[0].children[ta_select[0].selectedIndex].innerHTML);

	$(container+" select[name='tipo_ta']").change(function(event) {
	    var url = '';
	    url = '/ta/search_fragment_form?action=get_tipos&tipo_ta='+this.value;

	    $(container+" label[for='id_tipo_model']").html('Tipos de ' + this.children[this.selectedIndex].innerHTML);


	    var select = $(container+" select[name='tipo_model']");
	    select.empty();
	    $('<option value="">Carregando...</option>').appendTo(select);

	    $.get(url).done(function( data ) {
	        select.empty();
	        for(var item in data) {
	            for (var i in data[item])
	                  $('<option value="'+i+'">'+data[item][i]+'</option>').appendTo(select);
	        }
	        select.change(onChangeParamTA)
	    });
	});
	$(container+" input[name='num_ta'], "
			  + container+" input[name='ano_ta'], "
			  + container+" select[name='tipo_model'], "
	    + container+" input[name='busca_dispositivo']"
	).change(onChangeParamTA);

	$(container+" .btn-busca").click(onChangeParamTA);
}

var onChangeParamTA = function(event) {
    var tipo_ta = $("select[name='tipo_ta']").val();
    var tipo_model = $("select[name='tipo_model']").val();
    var num_ta = $("input[name='num_ta']").val();
    var ano_ta = $("input[name='ano_ta']").val();
    var rotulo_dispositivo = $("input[name='rotulo_dispositivo']").val();
    var busca_dispositivo = $("input[name='busca_dispositivo']").val();
    var dispositivo_ref = $("#id_dispositivo_ref").val();
    $('#id_dispositivo_ref').remove();

    if (dispositivo_ref == null)
        dispositivo_ref = ''

    var url = '';

    var formData = {
        'tipo_ta'            : tipo_ta,
        'tipo_model'         : tipo_model,
        'num_ta'             : num_ta,
        'ano_ta'             : ano_ta,
        'busca'              : busca_dispositivo,
        'rotulo'             : rotulo_dispositivo,
        'tipo_form'          : tipo_form,
        'tipo_select'        : tipo_select,
        'initial_ref'        : dispositivo_ref
    };

    url = '/ta/search_fragment_form';
    $('.result-busca-dispositivo').html('');
    insertWaitAjax('.result-busca-dispositivo')
    $.get(url, formData).done(function( data ) {
        $('.result-busca-dispositivo').html(data);
        //$("input[name='dispositivo_ref']").first().prop('checked', true);
    });
}
