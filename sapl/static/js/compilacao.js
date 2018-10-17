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
            var data_function = field.attr('data-function');

            var onChangeFieldSelects = function(event) {
                if (data_type_selection == 'checkbox') {
                    var tas = field.find('input[name="ta_select_all"]'); //tas - Textos Articulados
                    tas.off();

                    tas.on('change', function(event) {
                        $(this).closest('ul').find('input[name="'+data_field+'"]').prop("checked", this.checked);
                        //$(this).prop("checked", false);
                    });


                }
                else {
                    var dpts = field.find('input');
                    dpts.off()
                    dpts.attr('type', 'hidden');
                    $('<a class="text-danger">')
                        .insertBefore(dpts)
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
                var max_results = $("select[name='max_results']").val();
                var url = '';

                if (rotulo_dispositivo.length > 0 || texto_dispositivo.length > 0) {
                    $("input[name='dispositivos_internos']").prop('disabled', false);
                    $("input[name='dispositivos_internos']").closest('#div_id_dispositivos_internos').css('opacity','1');
                }
                else {
                    $("input[name='dispositivos_internos']").filter('[value="False"]').prop('checked', true);
                    $("input[name='dispositivos_internos']").prop('disabled', true);
                    $("input[name='dispositivos_internos']").closest('#div_id_dispositivos_internos').css('opacity','0.3');
                    dispositivos_internos = 'False';
                }
                var formData = {
                    'tipo_ta'               : tipo_ta,
                    'tipo_model'            : tipo_model,
                    'num_ta'                : num_ta,
                    'ano_ta'                : ano_ta,
                    'texto'                 : texto_dispositivo,
                    'rotulo'                : rotulo_dispositivo,
                    'dispositivos_internos' : dispositivos_internos,
                    'max_results'           : max_results,
                    'data_type_selection'   : data_type_selection,
                    'data_field'            : data_field,
                    'data_function'         : data_function,
                };

                url = '/ta/search_fragment_form';
                $('.result-busca-dispositivo').html('');
                insertWaitAjax('.result-busca-dispositivo')
                $.get(url, formData).done(function( data ) {
                    $('.result-busca-dispositivo').html(data);

                    if (data_type_selection == 'checkbox') {
                        var tas = $('.result-busca-dispositivo').find('input[name="ta_select_all"]');
                        tas.off();
                        tas.on('change', function(event) {
                            $(this).closest('ul').find('input[name="'+data_field+'"]').prop("checked", this.checked);
                        });
                    }

                });
            }

            var onKeyPressRotuloBuscaTextual = function(event) {
                var rotulo_dispositivo = $("input[name='rotulo_dispositivo']").val();
                var texto_dispositivo = $("input[name='texto_dispositivo']").val();
                var dispositivos_internos = $("input[name='dispositivos_internos']:checked").val();

                if (rotulo_dispositivo.length > 0 || texto_dispositivo.length > 0) {
                    $("input[name='dispositivos_internos']").prop('disabled', false);
                    $("input[name='dispositivos_internos']").closest('#div_id_dispositivos_internos').css('opacity','1');
                }
                else {
                    $("input[name='dispositivos_internos']").filter('[value="False"]').prop('checked', true);
                    $("input[name='dispositivos_internos']").prop('disabled', true);
                    $("input[name='dispositivos_internos']").closest('#div_id_dispositivos_internos').css('opacity','0.3');
                    dispositivos_internos = 'False';
                }
            }

            var button_ds = field.children("#button_ds");
            if (button_ds.length > 0)
                $(button_ds).remove();
            button_ds = $('<div id="button_ds" class="clearfix"/>');
            field.prepend(button_ds);

            var btn_open_search = $('<button>')
                .text(opts['text_button'])
                .attr('type','button')
                .attr('class','btn btn-sm btn-success btn-modal-open');
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
                            //select.change(onChangeParamTA)
                        });
                    });

                    /*modal_ds.find("input[name='num_ta'], "
                        +"input[name='ano_ta'], "
                        +"select[name='tipo_model'], "
                        +"input[name='texto_dispositivo'], "
                        +"input[name='dispositivos_internos'], "
                        +"input[name='rotulo_dispositivo']"
                    ).change(onChangeParamTA);*/
                    modal_ds.find("input[name='texto_dispositivo'], "
                        +"input[name='rotulo_dispositivo']")
                        .on('keyup', onKeyPressRotuloBuscaTextual)

                    modal_ds.find(".btn-busca").click(onChangeParamTA);

                    modal_ds.find("#btn-modal-select").click(function() {
                        // limpar selecionados se o tipo é radio
                        var listas = field.find('ul');
                        if (data_type_selection == 'radio')
                            listas.remove();

                        // adicionar itens selecionados na caixa modal
                        var selecionados = modal_ds.find('[name="'+data_field+'"]:checked');

                        // com base nos selecionados, limpa seus ta's removendo os não selecionados
                        selecionados.closest('ul').find('input:not(:checked)').filter('[name!="ta_select_all"]').closest('li').remove();

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

                        if ('post_selected' in opts)
                            opts['post_selected'](opts['params_post_selected'])

                    });

                    modal_ds.modal('show');
                    onChangeParamTA();
                })
            });
        });
    });
}
