function initTinymce(elements, readonly=false) {
    removeTinymce();
    var config_tinymce = {
        force_br_newlines : false,
        force_p_newlines : false,
        forced_root_block : '',
        plugins: ["table save code"],
        menubar: "edit format table tools",
        toolbar: "undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",
        tools: "inserttable",
        border_css: "/static/styles/style_tinymce.css",
        content_css: "/static/styles/style_tinymce.css",
    }

    if (readonly) {
      config_tinymce.readonly = 1;
      config_tinymce.menubar = false;
      config_tinymce.toolbar = false;
    }

    if (elements != null) {
        config_tinymce['elements'] = elements;
        config_tinymce['mode'] = "exact";
        }
    else
        config_tinymce['mode'] = "textareas";

    tinymce.init(config_tinymce);
}

function removeTinymce() {
    while (tinymce.editors.length > 0) {
        tinymce.remove(tinymce.editors[0]);
    }
}

function refreshDatePicker() {
    $.datepicker.setDefaults($.datepicker.regional['pt-BR']);
    $('.dateinput').datepicker();
}

function refreshMask() {
    $('.telefone').mask("(99) 9999-9999", {placeholder:"(__) ____ -____"});
    $('.cpf').mask("000.000.000-00", {placeholder:"___.___.___-__"});
    $('.cep').mask("00000-000", {placeholder:"_____-___"});
    $('.rg').mask("0.000.000", {placeholder:"_.___.___"});
    $('.titulo_eleitor').mask("0000.0000.0000.0000", {placeholder:"____.____.____.____"});
    $('.dateinput').mask('00/00/0000', {placeholder:"__/__/____"});
    $('.hora').mask("00:00", {placeholder:"hh:mm"});
    $('.hora_hms').mask("00:00:00", {placeholder:"hh:mm:ss"});
    $('.cronometro').mask("00:00", {placeholder:"mm:ss"});
}

function autorModal() {

  $(function() {
    var dialog = $("#modal_autor").dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 300,
      show: {
        effect: "blind",
        duration: 500},
      hide: {
        effect: "explode",
        duration: 500
      }
    });

    $("#button-id-limpar").click(function() {
      $("#nome_autor").text('');

      function clean_if_exists(fieldname) {
        if ($(fieldname).length > 0) {
          $(fieldname).val('');
        }
      }

      clean_if_exists("#id_autor");
      clean_if_exists("#id_autoria__autor");
    });

    $("#button-id-pesquisar").click(function() {
      $("#q").val('');
      $("#div-resultado").children().remove();
      $("#modal_autor").dialog( "open" );
      $("#selecionar").attr("hidden", "hidden");
    });

    $("#pesquisar").click(function() {
        var name_in_query = $("#q").val()
        var q_0 = "q_0=parlamentar_set__nome_parlamentar__icontains"
        var q_1 = "q_1=" + name_in_query
        query = q_0 + "&" + q_1

        $.get("/api/autor?" + query, function(data, status) {
            $("#div-resultado").children().remove();
            if (data.pagination.total_entries == 0) {
                $("#selecionar").attr("hidden", "hidden");
                $("#div-resultado").html(
                    "<span class='alert'><strong>Nenhum resultado</strong></span>");
                return;
            }

            var select = $(
                '<select id="resultados" \
                style="min-width: 90%; max-width:90%;" size="5"/>');

            data.results.forEach(function(item, index) {
                select.append($("<option>").attr('value', item.value).text(item.text));
            });



          $("#div-resultado").append("<br/>").append(select);
          $("#selecionar").removeAttr("hidden", "hidden");

          $("#selecionar").click(function() {
              res = $("#resultados option:selected");
              id = res.val();
              nome = res.text();

              $("#nome_autor").text(nome);

              // MateriaLegislativa pesquisa Autor via a tabela Autoria
              if ($('#id_autoria__autor').length) {
                $('#id_autoria__autor').val(id);
              }
              // Protocolo pesquisa a própria tabela de Autor
              if ($('#id_autor').length) {
                $("#id_autor").val(id);
              }

              dialog.dialog( "close" );
          });
        });
      });
    });

    /*function get_nome_autor(fieldname) {
      if ($(fieldname).length > 0) { // se campo existir
        if ($(fieldname).val() != "") { // e não for vazio
          var id = $(fieldname).val();
          $.get("/proposicao/get-nome-autor?id=" + id, function(data, status){
              $("#nome_autor").text(data.nome);
          });
        }
      }
    }

    get_nome_autor("#id_autor");
    get_nome_autor("#id_autoria__autor");*/
}

function OptionalCustomFrontEnd() {
    // Adaptações opcionais de layout com a presença de JS.
    // Não implementar customizações que a funcionalidade que fique dependente.
    var instance;
    if (!(this instanceof OptionalCustomFrontEnd)) {
        if (!instance) {
            instance = new OptionalCustomFrontEnd();
        }
        return instance;
    }
    instance = this;
    OptionalCustomFrontEnd = function() {
        return instance;
    }
    instance.customCheckBoxAndRadio = function() {
        $('[type=radio], [type=checkbox]').each(function() {
            var _this = $(this)
            var _controls = _this.closest('.controls');
            _controls && _controls.find(':file').length == 0 && !_controls.hasClass('controls-radio-checkbox') && _controls.addClass('controls-radio-checkbox');
            _controls.find(':file').length > 0 && _controls.addClass('controls-file');
        });
    }
    instance.customCheckBoxAndRadioWithoutLabel = function() {

        $('[type=radio], [type=checkbox]').each(function() {
            var _this = $(this);
            var _label = _this.closest('label');

            if (_label.length)
                return;

            if (this.id)
                _label = $('label[for='+this.id+']');
            else {
                _label = $('<label/>').insertBefore(this)
            }

            if (_label.length) {
                /*var _controls = _label.closest('.controls');

                if (!_controls.length) {
                    _controls = $('<div class="controls"/>').insertBefore(_label)
                    _controls.append(_label)
                }*/

                _label.addClass('checkbox-inline');
                _label.prepend(_this);
                _this.checkbox();
            }
        });
    }
    instance.init = function() {
        this.customCheckBoxAndRadio();
        this.customCheckBoxAndRadioWithoutLabel();
    }
    instance.init();
}

$(document).ready(function(){
    refreshDatePicker();
    refreshMask();
    autorModal();
    initTinymce("texto-rico");

    OptionalCustomFrontEnd();
});


function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}