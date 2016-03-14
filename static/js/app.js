
tinymce.init({selector:'textarea'});

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
    $('.hora').mask("00:00", {placeholder:"hh:mm"});
    $('.hora_hms').mask("00:00:00", {placeholder:"hh:mm:ss"});
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
        duration: 500				},
      hide: {
        effect: "explode",
        duration: 500
      }
    });

    $( "#button-id-limpar" ).click(function() {
      $("#nome_autor").text('');
      $("#id_autor").val(null);
    });

    $("#button-id-pesquisar").click(function() {
      $("#q").val('');
      $("#div-resultado").children().remove();
      $("#modal_autor").dialog( "open" );
      $("#selecionar").attr("hidden", "hidden");
    });

    $( "#pesquisar" ).click(function() {
        var query = $("#q").val()

        $.get("/proposicoes/pesquisar_autores?q="+ query, function(
          data, status){

          $("#div-resultado").children().remove();

          if (data.length == 0) {
            $("#selecionar").attr("hidden", "hidden");
            $("#div-resultado").html(
              "<span class='alert'><strong>Nenhum resultado</strong></span>");
            return;
          }

          var select = $(
            '<select id="resultados" \
            style="min-width: 90%; max-width:90%;" size="5"/>');

          for (i = 0; i < data.length; i++) {
              id = data[i][0];
              nome = data[i][1];

              select.append($("<option>").attr('value',id).text(nome));
          }

          $("#div-resultado").append("<br/>").append(select);
          $("#selecionar").removeAttr("hidden", "hidden");

          $("#selecionar").click(function() {
              res = $("#resultados option:selected");
              id = res.val();
              nome = res.text();

              $("#id_autor").val(id);
              $("#nome_autor").text(nome);

              dialog.dialog( "close" );
          });
        });
      });
    });
}

$(document).ready(function(){
    refreshDatePicker();
    refreshMask();
    autorModal();
});
