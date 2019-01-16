import jQuery from "jquery";

import dialog from "jquery-ui/ui/widgets/dialog";
import "jquery-ui/themes/base/all.css"

jQuery.dialog = dialog;

window.getCookie = function(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    var cookies = document.cookie.split(';');
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

window.autorModal = function() {

  jQuery(function() {
    var dialog = jQuery("#modal_autor").dialog({
      autoOpen: false,
      modal: true,
      width: 500,
      height: 340,
      show: {
        effect: "blind",
        duration: 500},
      hide: {
        effect: "explode",
        duration: 500
      }
    });

    jQuery("#button-id-limpar").click(function() {
      jQuery("#nome_autor").text('');

      function clean_if_exists(fieldname) {
        if (jQuery(fieldname).length > 0) {
          jQuery(fieldname).val('');
        }
      }

      clean_if_exists("#id_autor");
      clean_if_exists("#id_autoria__autor");
    });

    jQuery("#button-id-pesquisar").click(function() {
      jQuery("#q").val('');
      jQuery("#div-resultado").children().remove();
      jQuery("#modal_autor").dialog( "open" );
      jQuery("#selecionar").attr("hidden", "hidden");
    });

    jQuery("#pesquisar").click(function() {
        var name_in_query = jQuery("#q").val()
        //var q_0 = "q_0=nome__icontains"
        //var q_1 = name_in_query
        //query = q_1

        jQuery.get("/api/autor?q=" + name_in_query, function(data, status) {
            jQuery("#div-resultado").children().remove();
            if (data.pagination.total_entries == 0) {
                jQuery("#selecionar").attr("hidden", "hidden");
                jQuery("#div-resultado").html(
                    "<span class='alert'><strong>Nenhum resultado</strong></span>");
                return;
            }

            var select = jQuery(
                '<select id="resultados" \
                style="min-width: 90%; max-width:90%;" size="5"/>');

            data.results.forEach(function(item, index) {
                select.append(jQuery("<option>").attr('value', item.value).text(item.text));
            });

          jQuery("#div-resultado").append("<br/>").append(select);
          jQuery("#selecionar").removeAttr("hidden", "hidden");

          if (data.pagination.total_pages > 1)
              jQuery("#div-resultado").prepend('<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>');

          jQuery("#selecionar").click(function() {
              let res = jQuery("#resultados option:selected");
              let id = res.val();
              let nome = res.text();

              jQuery("#nome_autor").text(nome);

              // MateriaLegislativa pesquisa Autor via a tabela Autoria
              if (jQuery('#id_autoria__autor').length) {
                jQuery('#id_autoria__autor').val(id);
              }
              // Protocolo pesquisa a própria tabela de Autor
              if (jQuery('#id_autor').length) {
                jQuery("#id_autor").val(id);
              }

              dialog.dialog( "close" );
          });
        });
      });
    });

    /*function get_nome_autor(fieldname) {
      if (jQuery(fieldname).length > 0) { // se campo existir
        if (jQuery(fieldname).val() != "") { // e não for vazio
          var id = jQuery(fieldname).val();
          jQuery.get("/proposicao/get-nome-autor?id=" + id, function(data, status){
              jQuery("#nome_autor").text(data.nome);
          });
        }
      }
    }

    get_nome_autor("#id_autor");
    get_nome_autor("#id_autoria__autor");*/
};

window.autorModal();
