
tinymce.init({selector:'textarea'});
$(document).foundation();
 
$(document).ready(function(){


    $('.dateinput').fdatepicker({
        // TODO localize
        format: 'dd/mm/yyyy',
        language: 'pt',
        endDate: '31/12/2100',
        todayBtn: true
        });

    $('.telefone').mask("(99) 9999-9999", {placeholder:"(__) ____ -____"});
    $('.cpf').mask("000.000.000-00", {placeholder:"___.___.___-__"});
    $('.cep').mask("00000-000", {placeholder:"_____-___"});
    $('.rg').mask("0.000.000", {placeholder:"_.___.___"});
    $('.titulo_eleitor').mask("0000.0000.0000.0000", {placeholder:"____.____.____.____"});
    $('.hora').mask("00:00", {placeholder:"hh:mm"});
    $('.hora_hms').mask("00:00:00", {placeholder:"hh:mm:ss"});

    var href = location.href.split('?')
    $('.masthead .sub-nav a').each(function() {

        if (href.length >= 1) {
            if (href[0].endsWith($(this).attr('href')))
                $(this).parent().addClass('active')
        }
    });

});
