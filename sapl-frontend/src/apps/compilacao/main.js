//import JsDiff from "diff/dist/diff";


import compilacao from "./js/compilacao";
import compilacao_view from "./js/compilacao_view";
import _ from "lodash";

//import "./js/compilacao_notas";
//import "./js/compilacao_edit";

//require("imports-loader?this=>window!./js/compilacao.js");
//require("imports-loader?this=>window!./js/compilacao_edit.js");
//require("imports-loader?this=>window!./js/compilacao_notas.js");
//require("imports-loader?this=>window!./js/compilacao_view.js");


_.forEach(compilacao, function (func, key) {
  window[key] = func;

});
_.forEach(compilacao_view, function (func, key) {
  window[key] = func;

});


$(document).ready(function() {

  setTimeout(function() {
      var href = location.href.split('#')
      if (href.length == 2) {
          try {
              $('html, body').animate({
                  scrollTop: $('#dptt' + href[1] ).offset().top - window.innerHeight / 9
              }, 0);
          }
          catch(err) {
          }
      }
  }, 100);

  $("#btn_font_menos").click(function() {
      $(".dpt").css("font-size", "-=1");
  });
  $("#btn_font_mais").click(function() {
      $(".dpt").css("font-size", "+=1");
  });

  $(".dpt.bloco_alteracao .dpt").each(function() {
      var nivel = parseInt($(this).attr('nivel'));

      $(this).css('z-index', 15-nivel)

  });

});
