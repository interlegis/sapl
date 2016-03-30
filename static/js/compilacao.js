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
                    select.append($("<option>").attr('value',i).text(data[item][i]));
                    //$('<option value="'+i+'">'+data[item][i]+'</option>').appendTo(select);
            }
            select.change(onChangeParamTA)
        });
    });
    $(container+" input[name='num_ta'], "
        + container+" input[name='ano_ta'], "
        + container+" select[name='tipo_model'], "
        + container+" input[name='dispositivos_internos'], "
        + container+" input[name='texto_dispositivo'], "
        + container+" input[name='rotulo_dispositivo']"
    ).change(onChangeParamTA);

    $(container+" .btn-busca").click(onChangeParamTA);
}



function DispostivoSearch(opts) {

    $(function() {

        var container_ds = $('body').children("#container_ds");
        if (container_ds.length > 0)
            $(container_ds).remove();
        container_ds = $('<div id="container_ds"/>');
        $('body').prepend(container_ds);

        var fields = $("[data-sapl-ta='DispositivoSearch']");
        fields.each(function() {
            var field = $(this);
            var data_type_selection = field.attr('data-type-selection');
            var data_field = field.attr('data-field');

            var onChangeFieldSelects = function(event) {
                var selecionados = field.find('input');
                selecionados.off()

                if (data_type_selection == 'checkbox') {
                    selecionados.on('change', function(event) {
                        if (!this.checked) {
                            if ($(this).closest('ul').find('li').length == 2)
                                $(this).closest('ul').remove();
                            else
                                $(this).closest('li').remove();
                        }
                    });
                }
                else {
                    selecionados.attr('type', 'hidden');
                    $('<a class="text-danger" href="#">')
                        .insertBefore(selecionados)
                        .append($('<span class="glyphicon glyphicon-remove" aria-hidden="true"></span>'))
                        .on('click', function() {
                            if ($(this).closest('ul').find('li').length == 2)
                                $(this).closest('ul').remove();
                            else
                                $(this).closest('li').remove();
                        });
                }
            }
            onChangeFieldSelects();

            var onChangeParamTA = function(event) {
                var tipo_ta = $("select[name='tipo_ta']").val();
                var tipo_model = $("select[name='tipo_model']").val();
                var num_ta = $("input[name='num_ta']").val();
                var ano_ta = $("input[name='ano_ta']").val();
                var dispositivos_internos = $("input[name='dispositivos_internos']:checked").val();
                var rotulo_dispositivo = $("input[name='rotulo_dispositivo']").val();
                var texto_dispositivo = $("input[name='texto_dispositivo']").val();
                var url = '';
                var formData = {
                    'tipo_ta'               : tipo_ta,
                    'tipo_model'            : tipo_model,
                    'num_ta'                : num_ta,
                    'ano_ta'                : ano_ta,
                    'texto'                 : texto_dispositivo,
                    'rotulo'                : rotulo_dispositivo,
                    'dispositivos_internos' : dispositivos_internos,
                    'data_type_selection'   : data_type_selection,
                    'data_field'            : data_field,
                };

                url = '/ta/search_fragment_form';
                $('.result-busca-dispositivo').html('');
                insertWaitAjax('.result-busca-dispositivo')
                $.get(url, formData).done(function( data ) {
                    $('.result-busca-dispositivo').html(data);
                });
            }

            var button_ds = field.children("#button_ds");
            if (button_ds.length > 0)
                $(button_ds).remove();
            button_ds = $('<div id="button_ds" class="clearfix"/>');
            field.prepend(button_ds);

            var btn_open_search = $('<button>')
                .text(opts['text_button'])
                .attr('type','button')
                .attr('class','btn btn-sm btn-modal-open');
            button_ds.append(btn_open_search);
            btn_open_search.on('click', function() {
                $.get(opts['url_form'], function(data) {
                    container_ds.html(data);
                    var modal_ds = $('#modal-ds');

                    modal_ds.find("select[name='tipo_ta']").change(function(event) {
                        var url = '';
                        url = '/ta/search_fragment_form?action=get_tipos&tipo_ta='+this.value;
                        modal_ds.find("label[for='id_tipo_model']").html('Tipos de ' + this.children[this.selectedIndex].innerHTML);

                        var select = modal_ds.find("select[name='tipo_model']");
                        select.empty();
                        $('<option value="">Carregando...</option>').appendTo(select);

                        $.get(url).done(function( data ) {
                            select.empty();
                            for(var item in data) {
                                for (var i in data[item])
                                    select.append($("<option>").attr('value',i).text(data[item][i]));
                            }
                            select.change(onChangeParamTA)
                        });
                    });

                    modal_ds.find("input[name='num_ta'], "
                        +"input[name='ano_ta'], "
                        +"select[name='tipo_model'], "
                        +"input[name='texto_dispositivo'], "
                        +"input[name='dispositivos_internos'], "
                        +"input[name='rotulo_dispositivo']"
                    ).change(onChangeParamTA);

                    modal_ds.find(".btn-busca").click(onChangeParamTA);

                    modal_ds.find("#btn-modal-select").click(function() {
                        // limpar selecionados se o tipo é radio
                        var listas = field.find('ul');
                        if (data_type_selection == 'radio')
                            listas.remove();

                        // adicionar itens selecionados na caixa modal
                        var selecionados = modal_ds.find('[name="'+data_field+'"]:checked');

                        // com base nos selecionados, limpa seus ta's removendo os não selecionados
                        selecionados.closest('ul').find('input:not(:checked)').closest('li').remove();

                        selecionados.closest('ul').each(function() {
                            //insere na lista de selecionados os ta's não presentes
                            var ul_lista = field.find('#'+this.id);
                            if (ul_lista.length == 0) {
                                field.append(this);
                                return;
                            }

                            //insere os dispositivos não presentes
                            var inputs_for_this = $(this).find('input');

                            inputs_for_this.each(function() {
                                if (ul_lista.find("#"+this.id).length > 0)
                                    return;
                                ul_lista.append($(this).closest('li'));
                            });
                        });

                        onChangeFieldSelects();

                        modal_ds.modal('hide');
                    });

                    modal_ds.modal('show');
                    onChangeParamTA();
                })
            });
        });
    });
}
