!function(t){function e(e){for(var n,s,r=e[0],d=e[1],l=e[2],p=0,f=[];p<r.length;p++)s=r[p],Object.prototype.hasOwnProperty.call(o,s)&&o[s]&&f.push(o[s][0]),o[s]=0;for(n in d)Object.prototype.hasOwnProperty.call(d,n)&&(t[n]=d[n]);for(c&&c(e);f.length;)f.shift()();return a.push.apply(a,l||[]),i()}function i(){for(var t,e=0;e<a.length;e++){for(var i=a[e],n=!0,r=1;r<i.length;r++){var d=i[r];0!==o[d]&&(n=!1)}n&&(a.splice(e--,1),t=s(s.s=i[0]))}return t}var n={},o={compilacao:0},a=[];function s(e){if(n[e])return n[e].exports;var i=n[e]={i:e,l:!1,exports:{}};return t[e].call(i.exports,i,i.exports,s),i.l=!0,i.exports}s.m=t,s.c=n,s.d=function(t,e,i){s.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:i})},s.r=function(t){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},s.t=function(t,e){if(1&e&&(t=s(t)),8&e)return t;if(4&e&&"object"==typeof t&&t&&t.__esModule)return t;var i=Object.create(null);if(s.r(i),Object.defineProperty(i,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var n in t)s.d(i,n,function(e){return t[e]}.bind(null,n));return i},s.n=function(t){var e=t&&t.__esModule?function(){return t.default}:function(){return t};return s.d(e,"a",e),e},s.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},s.p="/static/sapl/frontend/";var r=window.webpackJsonp=window.webpackJsonp||[],d=r.push.bind(r);r.push=e,r=r.slice();for(var l=0;l<r.length;l++)e(r[l]);var c=d;a.push([1,"chunk-vendors"]),i()}({"0872":function(t,e,i){"use strict";(function(t){i("28a5"),i("5df3"),i("1c4c"),i("7514");var e=window.$;window.DispositivoEdit=function(){var t,i="textarea";if(!(this instanceof window.DispositivoEdit))return t||(t=new window.DispositivoEdit),t;t=this,window.DispositivoEdit=function(){return t},t.bindActionsEditorType=function(n){i=this.getAttribute("editortype"),window.SetCookie("editortype",i,30);var o=e(this).closest(".dpt").attr("pk");t.clearEditSelected(),t.triggerBtnDptEdit(o),n.preventDefault()},t.bindActionsClick=function(i){var n=this.getAttribute("pk"),o={action:this.getAttribute("action"),tipo_pk:this.getAttribute("tipo_pk"),perfil_pk:this.getAttribute("perfil_pk"),variacao:this.getAttribute("variacao"),pk_bloco:this.getAttribute("pk_bloco")},a=n+"/refresh";t.waitShow(),e.get(a,o).done((function(e){t.clearEditSelected(),null!=e.pk&&t.message(e)})).fail(t.waitHide).always(t.waitHide)},t.clearEditSelected=function(){e(".dpt-selected > .dpt-form").html(""),e(".dpt-actions, .dpt-actions-bottom").html(""),window.tinymce.remove(),e(".dpt-selected").removeClass("dpt-selected")},t.editDispositivo=function(i){var n=i.target.classList.contains("dpt-link")?i.target:i.target.parentElement.classList.contains("dpt-link")?i.target.parentElement:null;if(!(n&&n.getAttribute("href")&&n.getAttribute("href").length>0)){var o=e(this).closest(".dpt");if(o.hasClass("dpt-selected"))"editor-close"===this.getAttribute("action")&&t.clearEditSelected();else{t.clearEditSelected(),t.loadActionsEdit(o);var a=o.attr("formtype");o.on(a,t[a]),t.loadForm(o,a)}}},t.gc=function(){setTimeout((function(){e(".dpt:not(.dpt-selected) > .dpt-form").html("")}),500)},t.get_form_base=function(){var i=e(this);i.addClass("dpt-selected"),i.children().filter(".dpt-form").find("form").submit(t.onSubmitEditFormBase),t.scrollTo(i),i.off("get_form_base"),i.find(".btn-fechar").on("click",(function(e){t.clearEditSelected(),e.preventDefault()}));var n=i.find(".btns-excluir");i.find(".dpt-actions-bottom").first().append(n),n.find(".btn-outline-danger").on("click",t.bindActionsClick)},t.get_form_alteracao=function(){var i=e(this);i.off("get_form_alteracao"),e(".dpt-actions, .dpt-actions-bottom").html("");var n=i.children().filter(".dpt-form").children().first(),o=n[0].id_dispositivo_search_form.value;window.DispositivoSearch({url_form:o,text_button:"Selecionar"}),t.scrollTo(i),n.submit(t.onSubmitFormRegistraAlteracao),i.find(".btn-fechar").on("click",(function(e){t.clearEditSelected(),t.triggerBtnDptEdit(i.attr("pk")),e.preventDefault()}))},t.get_form_inclusao=function(){var i=e(this);i.off("get_form_inclusao"),e(".dpt-actions, .dpt-actions-bottom").html("");var n=i.children().filter(".dpt-form").children().first(),o=n[0].id_dispositivo_search_form.value;window.DispositivoSearch({url_form:o,text_button:"Selecionar",post_selected:t.allowed_inserts_registro_inclusao,params_post_selected:{pk_bloco:i.attr("pk")}}),t.scrollTo(i),n.submit(t.onSubmitFormRegistraInclusao),i.find(".btn-fechar").on("click",(function(e){t.clearEditSelected(),t.triggerBtnDptEdit(i.attr("pk")),e.preventDefault()}))},t.get_form_revogacao=function(){var i=e(this);i.off("get_form_revogacao"),e(".dpt-actions, .dpt-actions-bottom").html("");var n=i.children().filter(".dpt-form").children().first(),o=n[0].id_dispositivo_search_form.value;window.DispositivoSearch({url_form:o,text_button:"Selecionar"}),t.scrollTo(i),n.submit(t.onSubmitFormRegistraRevogacao),i.find(".btn-fechar").on("click",(function(){t.clearEditSelected(),t.triggerBtnDptEdit(i.attr("pk"))}))},t.allowed_inserts_registro_inclusao=function(i){var n=e("#id"+i.pk_bloco+" input[name='dispositivo_base_para_inclusao']");if(0!==n.length){var o=n[0].value,a={action:"get_actions_allowed_inserts_registro_inclusao",pk_bloco:i.pk_bloco},s=o+"/refresh";t.waitShow(),e.get(s,a).done((function(i){e(".allowed_inserts").html(i),e(".allowed_inserts").find(".btn-action").on("click",t.bindActionsClick)})).fail(t.waitHide).always(t.waitHide)}},t.loadActionsEdit=function(n){var o=n.attr("pk")+"/refresh?action=get_actions";e.get(o).done((function(o){n.find(".dpt-actions").first().html(o),n.find(".btn-action").on("click",t.bindActionsClick),n.find(".btn-compila").on("click",t.loadFormsCompilacao),n.find(".btn-editor-type").on("click",t.bindActionsEditorType),"construct"===i&&(n.find(".btn-group-inserts").first().addClass("open show"),n.find(".btn-group-inserts ul").first().addClass("show")),n.find(".btn-group-inserts button").mouseenter((function(t){n.find(".btn-group-inserts ul").removeClass("show"),n.find(".btn-group-inserts").removeClass("open show"),e(this.parentElement).addClass("open show"),e(this.parentElement).find("ul").addClass("show")})),n.find(".btn-group-inserts").mouseleave((function(t){n.find(".btn-group-inserts ul").removeClass("show"),n.find(".btn-group-inserts").removeClass("open show")})),t.gc()}))},t.loadForm=function(n,o){var a=n.attr("pk"),s=n.children().filter(".dpt-form");if(1===s.length){var r=a+"/refresh?action="+o;e.get(r).done((function(t){"construct"!==i&&(s.html(t),"tinymce"===i&&window.initTextRichEditor()),n.trigger(o)})).always((function(){t.waitHide()}))}},t.loadFormsCompilacao=function(i){var n=e(this).closest(".dpt"),o=this.getAttribute("action");n.on(o,t[o]),t.loadForm(n,o)},t.modalMessage=function(t,i,n){return null!==t&&""!==t&&(e("#modal-message #message").html(t),e("#modal-message").modal("show"),e("#modal-message, #modal-message .alert button").off(),e("#modal-message .alert").removeClass("alert-success alert-info alert-warning alert-danger alert-danger"),e("#modal-message .alert").addClass(i),null!=n&&e("#modal-message").on("hidden.bs.modal",n),e("#modal-message .alert button").on("click",(function(){e("#modal-message").modal("hide")})),!0)},t.message=function(i){if(void 0!==i.message)if(i.message.modal)t.modalMessage(i.message.value,"alert-"+i.message.type,(function(){t.waitShow(),t.refreshScreenFocusPk(i)}));else{if(t.refreshScreenFocusPk(i),!("message"in i))return;var n=e(".cp-notify");n.removeClass("hide");var o=n.find(".message");o.text(i.message.value),o.removeClass("bg-primary bg-success bg-info bg-warning bg-danger").addClass("bg-"+i.message.type),setTimeout((function(){n.addClass("hide")}),i.message.time?i.message.time:3e3)}else t.refreshScreenFocusPk(i)},t.offClicks=function(){e(".btn-dpt-edit").off()},t.onClicks=function(i){(null==i?e(".btn-dpt-edit"):e(i).find(".btn-dpt-edit")).on("click",t.editDispositivo)},t.onSubmitFormRegistraAlteracao=function(i){if(void 0===this.dispositivo_alterado)return t.modalMessage("Nenhum dispositivo selecionado","alert-info"),void(null!=i&&i.preventDefault());var n=void 0===this.dispositivo_alterado.length?[this.dispositivo_alterado]:Array.from(this.dispositivo_alterado),o={csrfmiddlewaretoken:this.csrfmiddlewaretoken.value,dispositivo_alterado:n.filter((function(t,e,i){return t.checked})).map((function(t){return t.value})),formtype:"get_form_alteracao"},a=e(this).closest(".dpt").attr("pk")+"/refresh";t.waitShow(),e.post(a,o).done((function(e){t.clearEditSelected(),null!=e.pk?t.message(e):alert("Erro na resposta!")})).always((function(){t.waitHide()})),null!=i&&i.preventDefault()},t.onSubmitFormRegistraInclusao=function(i){var n={csrfmiddlewaretoken:this.csrfmiddlewaretoken.value,dispositivo_base_para_inclusao:this.dispositivo_base_para_inclusao.value,formtype:"get_form_inclusao"},o=e(this).closest(".dpt").attr("pk")+"/refresh";t.waitShow(),e.post(o,n).done((function(e){t.clearEditSelected(),null!=e.pk?t.message(e):alert("Erro na resposta!")})).always((function(){t.waitHide()})),null!=i&&i.preventDefault()},t.onSubmitFormRegistraRevogacao=function(i){if(void 0===this.dispositivo_revogado)return t.modalMessage("Nenhum dispositivo selecionado","alert-info"),void(null!=i&&i.preventDefault());var n=void 0===this.dispositivo_revogado.length?[this.dispositivo_revogado]:Array.from(this.dispositivo_revogado),o={csrfmiddlewaretoken:this.csrfmiddlewaretoken.value,dispositivo_revogado:n.filter((function(t,e,i){return t.checked})).map((function(t){return t.value})),revogacao_em_bloco:this.revogacao_em_bloco.value,formtype:"get_form_revogacao"},a=e(this).closest(".dpt").attr("pk")+"/refresh";t.waitShow(),e.post(a,o).done((function(e){t.clearEditSelected(),null!=e.pk?t.message(e):alert("Erro na resposta!")})).always((function(){t.waitHide()})),null!=i&&i.preventDefault()},t.onSubmitEditFormBase=function(i){var n=this,o="",a="",s="",r=window.tinymce.get("id_texto"),d=window.tinymce.get("id_texto_atualizador");o=null!=r?r.getContent():this.id_texto.value,null!=d?a=d.getContent():"id_texto_atualizador"in this&&(a=this.id_texto_atualizador.value),"visibilidade"in this&&(s=this.visibilidade.value);var l={csrfmiddlewaretoken:this.csrfmiddlewaretoken.value,texto:o,texto_atualizador:a,visibilidade:s,formtype:"get_form_base"},c=e(this).closest(".dpt").attr("pk")+"/refresh";t.waitShow(),e.post(c,l).done((function(i){if("string"==typeof i){var o=e(n).closest(".dpt");return o=e("#"+o.replaceWith(i).attr("id")),t.onClicks(o),void t.waitHide()}t.clearEditSelected(),null!=i.pk?t.message(i):alert("Erro na resposta!")})).always((function(){t.waitHide()})),null!=i&&i.preventDefault()},t.refreshContent=function(i,n){if(0!==i.length){var o=i.shift(),a=o+"/refresh";e.get(a).done((function(a){var s=e("#id"+o).closest(".dpt");s=e("#"+s.replaceWith(a).attr("id")),t.onClicks(s),t.reloadFunctionsDraggables(),n>0&&t.triggerBtnDptEdit(n),t.refreshContent(i)}))}else t.waitHide()},t.refreshScreenFocusPk=function(e){if(t.waitShow(),-1===e.pai[0]){t.waitShow();var i=location.href.split("#")[0];location.href=i+"#"+e.pk,location.reload(!0)}else t.refreshContent(e.pai,e.pk)},t.reloadFunctionsDraggables=function(){e(".dpt-alts").sortable({revert:!0,distance:15,start:function(t,e){},stop:function(t,i){var n=i.item.attr("pk"),o=i.item.closest(".dpt-alts").closest(".dpt").attr("pk"),a=n+"/refresh?action=json_drag_move_dpt_alterado&index="+i.item.index()+"&bloco_pk="+o;e.get(a).done((function(t){}))}}),e(".dpt-alts .dpt").draggable({connectToSortable:".dpt-alts",revert:"invalid",zIndex:1,distance:15,drag:function(t,i){e(".dpt-alts").addClass("drag")},stop:function(t,i){e(".dpt-alts").removeClass("drag")}}),e(".dpt-alts").disableSelection()},t.scrollTo=function(t){try{e("html, body").animate({scrollTop:t.offset().top-window.innerHeight/9},100)}catch(t){}},t.triggerBtnDptEdit=function(t){var i=e("#id"+t+" > .dpt-text.btn-dpt-edit");0===i.length&&(i=e("#id"+t+" > .dpt-actions-fixed > .btn-dpt-edit")),i.trigger("click")},t.waitHide=function(){e("#wait_message").addClass("displaynone")},t.waitShow=function(){e("#wait_message").removeClass("displaynone")},t.init=function(){e(".dpt-actions-fixed").first().css("opacity","1"),null!==(i=window.ReadCookie("editortype"))&&""!==i||(i="textarea",window.SetCookie("editortype",i,30)),t.offClicks(),t.onClicks(),t.reloadFunctionsDraggables();var n=location.href.split("#");2===n.length&&""!==n[1]&&t.triggerBtnDptEdit(n[1]),e("main").click((function(e){e.target!==this&&e.target!==this.firstElementChild||t.clearEditSelected()})),t.waitHide()},t.init()},e(document).ready((function(){t(".cpe").length>0&&window.DispositivoEdit()}))}).call(this,i("1157"))},1:function(t,e,i){t.exports=i("6ccd")},"4a8b":function(t,e,i){"use strict";i("7514");var n=window.$;function o(t){n(t).append('<div style="text-align:center;"><i style="font-size: 200%;" class="fa fa-refresh fa-spin"></i></div>')}e.a={SetCookie:function(t,e,i){var n=new Date,o=new Date;null!==i&&0!==i||(i=1),o.setTime(n.getTime()+864e5*i),document.cookie=t+"="+escape(e)+";expires="+o.toGMTString()},ReadCookie:function(t){var e=" "+document.cookie,i=e.indexOf(" "+t+"=");if(-1===i&&(i=e.indexOf(";"+t+"=")),-1===i||""===t)return"";var n=e.indexOf(";",i+1);return-1===n&&(n=e.length),unescape(e.substring(i+t.length+2,n))},insertWaitAjax:o,DispositivoSearch:function(t){n((function(){var e={},i=n("body").children("#container_ds");i.length>0&&n(i).remove(),i=n('<div id="container_ds"/>'),n("body").prepend(i),n('[data-sapl-ta="DispositivoSearch"]').each((function(){var a=n(this),s=a.attr("data-type-selection"),r=a.attr("data-field"),d=a.attr("data-function"),l=function(t){if("checkbox"===s){var e=a.find('input[name="ta_select_all"]');e.off(),e.on("change",(function(t){n(this).closest("ul").find('input[name="'+r+'"]').prop("checked",this.checked)}))}else{var i=a.find("input");i.off(),i.attr("type","hidden"),n('<a class="text-danger">').insertBefore(i).append(n('<span aria-hidden="true">&times;</span>')).on("click",(function(){2===n(this).closest("ul").find("li").length?n(this).closest("ul").remove():n(this).closest("li").remove()}))}};l();var c=function(t){var i=n('select[name="tipo_ta"]').val(),a=n('select[name="tipo_model"]').val(),l=n('input[name="num_ta"]').val(),c=n('input[name="ano_ta"]').val(),p=n('input[name="dispositivos_internos"]:checked').val(),f=n('input[name="rotulo_dispositivo"]').val(),u=n('input[name="texto_dispositivo"]').val(),m=n('select[name="max_results"]').val();f.length>0||u.length>0?(n('input[name="dispositivos_internos"]').prop("disabled",!1),n('input[name="dispositivos_internos"]').each((function(t,e){e.parentElement.classList.remove("disabled")})),n('input[name="dispositivos_internos"]').closest("#div_id_dispositivos_internos").css("opacity","1")):(n('input[name="dispositivos_internos"]').filter('[value="False"]').prop("checked",!0),n('input[name="dispositivos_internos"]').prop("disabled",!0),n('input[name="dispositivos_internos"]').each((function(t,e){e.parentElement.classList.add("disabled")})),n('input[name="dispositivos_internos"]').closest("#div_id_dispositivos_internos").css("opacity","0.3"),p="False"),e={tipo_ta:i,tipo_model:a,num_ta:l,ano_ta:c,texto:u,rotulo:f,dispositivos_internos:p,max_results:m,data_type_selection:s,data_field:r,data_function:d},window.localStorage.setItem("dispositivo_search_form_data",JSON.stringify(e)),n(".result-busca-dispositivo").html(""),o(".result-busca-dispositivo"),n.get("/ta/search_fragment_form",e).done((function(t){if(n(".result-busca-dispositivo").html(t),"checkbox"===s){var e=n(".result-busca-dispositivo").find('input[name="ta_select_all"]');e.off(),e.on("change",(function(t){n(this).closest("ul").find('input[name="'+r+'"]').prop("checked",this.checked)}))}}))},p=function(t){var e=n('input[name="rotulo_dispositivo"]').val(),i=n('input[name="texto_dispositivo"]').val();e.length>0||i.length>0?(n('input[name="dispositivos_internos"]').prop("disabled",!1),n('input[name="dispositivos_internos"]').each((function(t,e){e.parentElement.classList.remove("disabled")})),n('input[name="dispositivos_internos"]').closest("#div_id_dispositivos_internos").css("opacity","1")):(n('input[name="dispositivos_internos"]').filter('[value="False"]').prop("checked",!0),n('input[name="dispositivos_internos"]').prop("disabled",!0),n('input[name="dispositivos_internos"]').each((function(t,e){e.parentElement.classList.add("disabled")})),n('input[name="dispositivos_internos"]').closest("#div_id_dispositivos_internos").css("opacity","0.3"))},f=a.children("#buttonDs");f.length>0&&n(f).remove(),f=n('<div id="buttonDs" class="clearfix"/>'),a.prepend(f);var u=n("<button>").text(t.text_button).attr("type","button").attr("class","btn btn-sm btn-success btn-modal-open");f.append(u),u.on("click",(function(){n.get(t.url_form,(function(o){i.html(o);var d=n("#modal-ds");d.find('select[name="tipo_ta"]').change((function(t){var i;i="/ta/search_fragment_form?action=get_tipos&tipo_ta="+this.value,d.find('label[for="id_tipo_model"]').html("Tipos de "+this.children[this.selectedIndex].innerHTML);var o=d.find('select[name="tipo_model"]');o.empty(),n('<option value="">Carregando...</option>').appendTo(o),n.get(i).done((function(t){for(var i in o.empty(),t)for(var a in t[i])o.append(n("<option>").attr("value",a).text(t[i][a]));setTimeout((function(){n('select[name="tipo_model"]').val(e.tipo_model)}),200)}))})),d.find('input[name="texto_dispositivo"], input[name="rotulo_dispositivo"]').on("keyup",p),d.find(".btn-busca").click(c),d.find("#btn-modal-select").click((function(){var e=a.find("ul");"radio"===s&&e.remove();var i=d.find('[name="'+r+'"]:checked');i.closest("ul").find("input:not(:checked)").filter('[name!="ta_select_all"]').closest("li").remove(),i.closest("ul").each((function(){var t=a.find("#"+this.id);0!==t.length?n(this).find("input").each((function(){t.find("#"+this.id).length>0||t.append(n(this).closest("li"))})):a.append(this)})),l(),d.modal("hide"),"post_selected"in t&&t.post_selected(t.params_post_selected)}));try{e=JSON.parse(window.localStorage.getItem("dispositivo_search_form_data")),n('input[name="num_ta"]').val(e.num_ta),n('input[name="ano_ta"]').val(e.ano_ta),n('input[name="rotulo_dispositivo"]').val(e.rotulo),n('input[name="texto_dispositivo"]').val(e.texto),n('select[name="max_results"]').val(e.max_results)}catch(t){}setTimeout((function(){try{n('select[name="tipo_ta"]').val(e.tipo_ta),n('select[name="tipo_ta"]').trigger("change")}catch(t){}}),200),d.modal("show")}))}))}))}))}}},"6ccd":function(t,e,i){"use strict";i.r(e),function(t,e){i("28a5"),i("ac6a"),i("cadf"),i("551c"),i("f751"),i("097d"),i("6d5e");var n=i("4a8b"),o=i("a0fe"),a=i("aa48");i("0872");t.forEach(t.merge(t.merge(n.a,a.a),o.a),(function(t,e){window[e]=t})),e(document).ready((function(){setTimeout((function(){var t=location.href.split("#");if(2===t.length)try{e("html, body").animate({scrollTop:e("#dptt"+t[1]).offset().top-window.innerHeight/9},0)}catch(t){}}),100),e("#btn_font_menos").click((function(){e(".dpt").css("font-size","-=1")})),e("#btn_font_mais").click((function(){e(".dpt").css("font-size","+=1")})),e(".dpt.bloco_alteracao .dpt").each((function(){var t=parseInt(e(this).attr("nivel"));e(this).css("z-index",15-t)})),e(".cp-linha-vigencias > li:not(:first-child):not(:last-child) > a").click((function(t){e(".cp-linha-vigencias > li").removeClass("active"),e(this).closest("li").addClass("active"),t.preventDefault()})),e("main").click((function(t){t.target!==this&&t.target!==this.firstElementChild||e(".cp-linha-vigencias > li").removeClass("active")})),window.onReadyNotasVides()}))}.call(this,i("2ef0"),i("1157"))},"6d5e":function(t,e,i){},a0fe:function(t,e,i){"use strict";(function(t){i("ac6a"),i("386d");var n=window.$,o=i("bf68");function a(e){"function"==typeof t&&e instanceof t&&(e=e[0]);var i=e.getBoundingClientRect();return i.top>=0&&i.left>=0&&i.bottom<=(window.innerHeight||document.documentElement.clientHeight)&&i.right<=(window.innerWidth||document.documentElement.clientWidth)}e.a={isElementInViewport:a,textoMultiVigente:function(t,e){for(var i=null,s=n(".dptt"),r=0;r<s.length;r++)if(!n(s[r]).hasClass("displaynone")&&a(s[r])){i=r+1<s.length?s[r+1]:s[r];break}if(n(".cp .tipo-vigencias a").removeClass("active"),n(t).addClass("active"),n(".dptt.desativado").removeClass("displaynone"),n(".dtxt").removeClass("displaynone"),n(".dtxt.diff").remove(),n(".nota-alteracao").removeClass("displaynone"),e&&n('.dtxt[id^="da"').each((function(){if(!(n(this).html().search(/<\/\w+>/g)>0)){var t=n(this).attr("pk"),e=n(this).attr("pks"),i=n("#d"+e).contents().filter((function(){return this.nodeType===Node.TEXT_NODE})),a=n("#da"+t).contents().filter((function(){return this.nodeType===Node.TEXT_NODE})),s=o.diffWordsWithSpace(n(i).text(),n(a).text());if(s.length>0){n("#d"+e).closest(".desativado").addClass("displaynone");var r=n("#da"+t).clone();n("#da"+t).after(r),n("#da"+t).addClass("displaynone"),n(r).addClass("diff").html(""),s.forEach((function(t){var e=document.createElement("span"),i=t.value;t.removed?(n(e).addClass("desativado"),i+=" "):t.added&&n(e).addClass("added"),e.appendChild(document.createTextNode(i)),n(r).append(e)}))}}})),i)try{n("html, body").animate({scrollTop:n(i).parent().offset().top-60},0)}catch(t){}},textoVigente:function(t,e){for(var i=null,o=n(".dptt"),s=0;s<o.length;s++)if(!n(o[s]).hasClass("displaynone")&&a(o[s])){i=s+1<o.length?o[s+1]:o[s];break}if(n(".cp .tipo-vigencias a").removeClass("active"),n(t).addClass("active"),n(".dptt.desativado").addClass("displaynone"),n(".nota-alteracao").removeClass("displaynone"),e||n(".nota-alteracao").addClass("displaynone"),i)try{n("html, body").animate({scrollTop:n(i).parent().offset().top-60},0)}catch(t){}}}}).call(this,i("1157"))},aa48:function(t,e,i){"use strict";var n=window.$;function o(t,e){n("html, body").animate({scrollTop:n("#dne"+t).offset().top-window.innerHeight/5},300),window.refreshDatePicker(),n("#dne"+t+" #button-id-submit-form").click(a),n("#dne"+t+" .btn-close-container").click((function(){n(this).closest(".dne-nota").removeClass("dne-nota"),n(this).closest(".dne-form").html("")})),"nota"===e?n("#dne"+t+' select[name="tipo"]').change((function(e){var i;i="text/"+t+"/nota/create?action=modelo_nota&id_tipo="+this.value,n.get(i).done((function(e){n("#dne"+t+' textarea[name="texto"]').val(e)}))})):"vide"===e&&window.DispositivoSearch({url_form:"/ta/search_form",text_button:"Definir Dispositivo"})}function a(t){var e,i="",a="nota",s=n("#id_dispositivo").val();void 0===s&&(s=n("#id_dispositivo_base").val(),a="vide"),e=n("#id_pk").val(),i="text/"+s+"/"+a+"/",i+=null===e||""===e?"create":e+"/edit",n.post(i,n("#dne"+s+" form").serialize(),(function(t){if("string"==typeof t)if(t.indexOf("<form")>=0)n("#dne"+s+" .dne-form").html(t),o(s,a);else{n("#dne"+s+" .dne-form").closest(".dpt").html(t),r();try{n("html, body").animate({scrollTop:n("#dne"+s).offset().top-window.innerHeight/3},300)}catch(t){}}}))}function s(t){var e=n(t).attr("model"),i=n(t).closest(".dn").attr("pk"),o=n(t).attr("pk"),a="text/"+i+"/"+e+"/"+o+"/delete";n.get(a,(function(t){n("#dne"+i+" .dne-form").closest(".dpt").html(t),r()}))}function r(){n(".dne-nota").removeClass("dne-nota"),n(".dne-form").html(""),n(".dne .btn-action").off(),n(".dn .btn-action").off(),n(".dne .btn-action, .dn .btn-action").not(".btn-nota-delete").not(".btn-vide-delete").click((function(){!function(t){var e="",i=n(t).attr("model"),a=n(".dne-nota .dne-form").closest(".dne").attr("pk");if(null!=a&&(n("#dne"+a).removeClass("dne-nota"),n("#dne"+a+" .dne-form").html("")),t.className.indexOf("create")>=0)e="text/"+(a=n(t).attr("pk"))+"/"+i+"/create";else if(t.className.indexOf("edit")>=0){var s=n(t).attr("pk");e="text/"+(a=n(t).closest(".dn").attr("pk"))+"/"+i+"/"+s+"/edit"}n("#dne"+a).addClass("dne-nota"),n.get(e).done((function(t){n("#dne"+a+" .dne-form").html(t),o(a,i)})).fail((function(){r()}))}(this)})),n(".dn .btn-nota-delete, .dn .btn-vide-delete").click((function(){s(this)}))}e.a={onEventsDneExec:o,onSubmitEditNVForm:a,onDelete:s,onReadyNotasVides:r}}});