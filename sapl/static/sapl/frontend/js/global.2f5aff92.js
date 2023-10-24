/*! For license information please see global.2f5aff92.js.LICENSE.txt */
(()=>{var d,c,e,a={5228:(e,t,a)=>{var i=a(9755),o=a(6486);a(3210),a(9554),a(1539),a(4747),window.refreshDatePicker=function(){i.datepicker.setDefaults(i.datepicker.regional["pt-BR"]),i(".dateinput").datepicker();var e=document.querySelectorAll(".dateinput");o.each(e,function(e,t){e.setAttribute("autocomplete","off")})},window.getCookie=function(e){var t=null;if(document.cookie&&""!==document.cookie)for(var a=document.cookie.split(";"),o=0;o<a.length;o++){var r=i.trim(a[o]);if(r.substring(0,e.length+1)===e+"="){t=decodeURIComponent(r.substring(e.length+1));break}}return t},window.autorModal=function(){i(function(){var a=i("#modal_autor").dialog({autoOpen:!1,modal:!0,width:500,height:340,show:{effect:"blind",duration:500},hide:{effect:"explode",duration:500}});i("#button-id-limpar").click(function(){function e(e){0<i(e).length&&i(e).val("")}i("#nome_autor").text(""),e("#id_autor"),e("#id_autoria__autor"),e("#id_autorianorma__autor")}),i("#button-id-pesquisar").click(function(){i("#q").val(""),i("#div-resultado").children().remove(),i("#modal_autor").dialog("open"),i("#selecionar").attr("hidden","hidden")}),i("#pesquisar").click(function(){var e={q:i("#q").val()};i.get("/api/base/autor",e,function(e){var t;i("#div-resultado").children().remove(),0===e.pagination.total_entries?(i("#selecionar").attr("hidden","hidden"),i("#div-resultado").html("<span class='alert'><strong>Nenhum resultado</strong></span>")):(t=i('<select id="resultados" style="min-width: 90%; max-width:90%;" size="5"/>'),e.results.forEach(function(e){t.append(i("<option>").attr("value",e.id).text(e.nome))}),i("#div-resultado").append("<br/>").append(t),i("#selecionar").removeAttr("hidden","hidden"),1<e.pagination.total_pages&&i("#div-resultado").prepend("<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>"),i("#selecionar").click(function(){var e=i("#resultados option:selected"),t=e.val(),e=e.text();i("#nome_autor").text(e),i("#id_autoria__autor").length&&i("#id_autoria__autor").val(t),i("#id_autor").length&&i("#id_autor").val(t),i("#id_autorianorma__autor").length&&i("#id_autorianorma__autor").val(t),a.dialog("close")}))})})})},window.refreshMask=function(){i(".telefone").mask("(99) 9999-9999",{placeholder:"(__) ____ -____"}),i(".cpf").mask("000.000.000-00",{placeholder:"___.___.___-__"}),i(".cep").mask("00000-000",{placeholder:"_____-___"}),i(".rg").mask("0.000.000",{placeholder:"_.___.___"}),i(".titulo_eleitor").mask("0000.0000.0000.0000",{placeholder:"____.____.____.____"}),i(".dateinput").mask("00/00/0000",{placeholder:"__/__/____"}),i(".hora, input[name=hora_inicio], input[name=hora_fim], input[name=hora]").mask("00:00",{placeholder:"hh:mm"}),i(".hora_hms").mask("00:00:00",{placeholder:"hh:mm:ss"}),i(".timeinput").mask("00:00:00",{placeholder:"hh:mm:ss"}),i(".cronometro").mask("00:00:00",{placeholder:"hh:mm:ss"})}},4124:(e,t,a)=>{var p,f,o=a(9755),r=a(9755),i=(a(4916),a(5306),a(3650),a(9600),a(9826),a(1539),a(1058),p=o,{init:function(){p("input.image-ratio").each(function(){var e,t,a,o,r,i,n,s,l,d,c,u=p(this),h=u.attr("name").replace(u.data("my-name"),u.data("image-field")),h=p("input.crop-thumb[data-field-name="+h+"]:first");h.length&&void 0!==h.data("thumbnail-url")?(h.data("hide-field")&&h.hide().parents("div.form-row:first").hide(),e=u.attr("id")+"-image",n=(t=h.data("org-width"))<(a=h.data("org-height")),i=(o=u.data("min-width"))<(r=u.data("min-height")),!0===u.data("adapt-rotation")&&n!=i&&(n=o,o=r,r=n),i=p("<img>",{id:e,src:h.data("thumbnail-url")}),n={minSize:[5,5],keySupport:!1,trueSize:[t,a],onSelect:function(e){var t=s;{var a,o,r,i,o;t.data("size-warning")&&(a=e,r=(o=t).siblings(".jcrop-holder"),i=o.data("min-width"),o=o.data("min-height"),a.w<i||a.h<o?r.addClass("size-warning"):r.removeClass("size-warning"))}t.val(new Array(Math.round(e.x),Math.round(e.y),Math.round(e.x2),Math.round(e.y2)).join(","))},addClass:(s=u).data("size-warning")&&(t<o||a<r)?"size-warning jcrop-image":"jcrop-image"},u.data("ratio")&&(n.aspectRatio=u.data("ratio")),u.data("box_max_width")&&(n.boxWidth=u.data("box_max_width")),u.data("box_max_height")&&(n.boxHeight=u.data("box_max_height")),l=!1,"-"==u.val()[0]&&(l=!0,u.val(u.val().substr(1))),u.val()?d=function(e){if(""!==e)return e=e.split(","),[parseInt(e[0],10),parseInt(e[1],10),parseInt(e[2],10),parseInt(e[3],10)]}(u.val()):(d=function(e,t,a,o){var r,e=e/t;if(a<o*e)return[0,r=Math.round((o-a/e)/2),a,o-r];return[r=Math.round((a-o*e)/2),0,a-r,o]}(o,r,t,a),u.val(d.join(","))),p.extend(n,{setSelect:d}),u.hide().after(i),p("#"+e).Jcrop(n,function(){f[e]=this}),!0===u.data("allow-fullsize")&&(l&&(f[e].release(),u.val("-"+u.val())),h=p('<div class="field-box allow-fullsize"><input type="checkbox" id="'+(c="allow-fullsize-"+e)+'" name="'+c+'"'+(l?"":' checked="checked"')+"></div>"),u.parent().find(".help").length?h.insertBefore(u.parent().find(".help")):h.appendTo(u.parent()),p("#"+c).click(function(){l=!0===l?(u.val(u.val().substr(1)),f[e].setSelect(u.val().split(",")),!1):(u.val("-"+u.val()),f[e].release(),!0)}),u.parent().find(".jcrop-tracker").mousedown(function(){l&&(p("#"+c).attr("checked","checked"),l=!1)}))):u.hide().parents("div.form-row:first").hide()})},jcrop:f={}});window.image_cropping=i,o(function(){r(function(){i.init()})})},4730:(e,t,a)=>{var Me,o=a(9755),Oe=a(1692).default;a(2564),a(4916),a(7601),a(4812),(Me=o).Jcrop=function(e,t){function x(e){return Math.round(e)+"px"}function k(e){return S.baseClass+"-"+e}function l(e){e=Me(e).offset();return[e.left,e.top]}function a(e){return[e.pageX-z[0],e.pageY-z[1]]}function j(e){"object"!=Oe(e)&&(e={}),S=Me.extend(S,e),Me.each(["onChange","onSelect","onRelease","onDblClick"],function(e,t){"function"!=typeof S[t]&&(S[t]=function(){})})}function H(e,t,a){if(z=l(_),O.setCursor("move"===e?e:e+"-resize"),"move"===e)return O.activateHandlers((o=t,fe.watchKeys(),function(e){F.moveOffset([e[0]-o[0],e[1]-o[1]]),o=e,M.update()}),N,a);var o,r,i,t=F.getFixed(),n=L(e),s=F.getCorner(L(n));F.setPressed(F.getCorner(n)),F.setCurrent(s),O.activateHandlers((r=e,i=t,function(e){if(S.aspectRatio)switch(r){case"e":case"w":e[1]=i.y+1;break;case"n":case"s":e[0]=i.x+1}else switch(r){case"e":case"w":e[1]=i.y2;break;case"n":case"s":e[0]=i.x2}F.setCurrent(e),M.update()}),N,a)}function L(e){switch(e){case"n":return"sw";case"s":case"e":return"nw";case"w":return"ne";case"ne":return"sw";case"nw":return"se";case"se":return"nw";case"sw":return"ne"}}function B(t){return function(e){return S.disabled||"move"===t&&!S.allowMove||(z=l(_),o=!0,H(t,a(e)),e.stopPropagation(),e.preventDefault()),!1}}function E(e,t,a){var o=e.width(),r=e.height();a<(r=t<o&&0<t?(o=t)/e.width()*e.height():r)&&0<a&&(o=(r=a)/e.height()*e.width()),b=e.width()/o,v=e.height()/r,e.width(o).height(r)}function q(e){return{x:e.x*b,y:e.y*v,x2:e.x2*b,y2:e.y2*v,w:e.w*b,h:e.h*v}}function N(e){var t=F.getFixed();t.w>S.minSelect[0]&&t.h>S.minSelect[1]?(M.enableHandles(),M.done()):M.release(),O.setCursor(S.allowSelect?"crosshair":"default")}function J(e){var t;return S.disabled||S.allowSelect&&(o=!0,z=l(_),M.disableHandles(),O.setCursor("crosshair"),t=a(e),F.setPressed(t),M.update(),O.activateHandlers(V,N,"touch"===e.type.substring(0,5)),fe.watchKeys(),e.stopPropagation(),e.preventDefault()),!1}function V(e){F.setCurrent(e),M.update()}function U(){var e=Me("<div></div>").addClass(k("tracker"));return de&&e.css({opacity:0,backgroundColor:"white"}),e}function G(e){K([e[0]/b,e[1]/v,e[2]/b,e[3]/v]),S.onSelect.call(D,q(F.getFixed())),M.enableHandles()}function K(e){F.setPressed([e[0],e[1]]),F.setCurrent([e[2],e[3]]),M.update()}function W(){S.disabled=!0,M.disableHandles(),M.setCursor("default"),O.setCursor("default")}function Y(){S.disabled=!1,X()}function Q(e,t,a){t=t||S.bgColor;S.bgFade&&Me.fx.step.hasOwnProperty("backgroundColor")&&S.fadeTime&&!a?e.animate({backgroundColor:t},{queue:!1,duration:S.fadeTime}):e.css("backgroundColor",t)}function X(e){S.allowResize?e?M.enableOnly():M.enableHandles():M.disableHandles(),O.setCursor(S.allowSelect?"crosshair":"default"),M.setCursor(S.allowMove?"move":"default"),S.hasOwnProperty("trueSize")&&(b=S.trueSize[0]/y,v=S.trueSize[1]/C),S.hasOwnProperty("setSelect")&&(G(S.setSelect),M.done(),delete S.setSelect),R.refresh(),S.bgColor!=he&&(Q(S.shade?R.getShades():c,S.shade&&S.shadeColor||S.bgColor),he=S.bgColor),pe!=S.bgOpacity&&(pe=S.bgOpacity,S.shade?R.refresh():M.setBgOpacity(pe)),p=S.maxSize[0]||0,Z=S.maxSize[1]||0,$=S.minSize[0]||0,ee=S.minSize[1]||0,S.hasOwnProperty("outerImage")&&(_.attr("src",S.outerImage),delete S.outerImage),M.refresh()}var _,p,Z,$,ee,b,v,o,te,r,ae,oe,re,ie,i,n,s,ne,se,f,m,g,w,S=Me.extend({},Me.Jcrop.defaults),le=navigator.userAgent.toLowerCase(),de=/msie/.test(le),le=/msie [1-6]\./.test(le),t=("object"!=Oe(e)&&(e=Me(e)[0]),j(t="object"!=Oe(t)?{}:t),{border:"none",visibility:"visible",margin:0,padding:0,position:"absolute",top:0,left:0}),d=Me(e),ce=!0,y=("IMG"==e.tagName?(0!=d[0].width&&0!=d[0].height?(d.width(d[0].width),d.height(d[0].height)):((ae=new Image).src=d[0].src,d.width(ae.width),d.height(ae.height)),(_=d.clone().removeAttr("id").css(t).show()).width(d.width()),_.height(d.height()),d.after(_).hide()):(_=d.css(t).show(),ce=!1,null===S.shade&&(S.shade=!0)),E(_,S.boxWidth,S.boxHeight),_.width()),C=_.height(),c=Me("<div />").width(y).height(C).addClass(k("holder")).css({position:"relative",backgroundColor:S.bgColor}).insertAfter(d).append(_),I=(S.addClass&&c.addClass(S.addClass),Me("<div />")),ue=Me("<div />").width("100%").height("100%").css({zIndex:310,position:"absolute",overflow:"hidden"}),A=Me("<div />").width("100%").height("100%").css("zIndex",320),T=Me("<div />").css({position:"absolute",zIndex:600}).dblclick(function(){var e=F.getFixed();S.onDblClick.call(D,e)}).insertBefore(_).append(ue,A),u=(ce&&(I=Me("<img />").attr("src",_.attr("src")).css(t).width(y).height(C),ue.append(I)),le&&T.css({overflowY:"hidden"}),S.boundary),h=U().width(y+2*u).height(C+2*u).css({position:"absolute",top:x(-u),left:x(-u),zIndex:290}).mousedown(J),he=S.bgColor,pe=S.bgOpacity,z=l(_),P={createDragger:function(t){return function(e){return S.disabled||"move"===t&&!S.allowMove||(z=l(_),o=!0,H(t,a(P.cfilter(e)),!0),e.stopPropagation(),e.preventDefault()),!1}},newSelection:function(e){return J(P.cfilter(e))},cfilter:function(e){return e.pageX=e.originalEvent.changedTouches[0].pageX,e.pageY=e.originalEvent.changedTouches[0].pageY,e},isSupported:Re,support:!0===S.touchSupport||!1===S.touchSupport?S.touchSupport:Re()},F=(w=g=m=f=0,{flipCoords:Pe,setPressed:function(e){e=ze(e),g=f=e[0],w=m=e[1]},setCurrent:function(e){e=ze(e),ne=e[0]-g,se=e[1]-w,g=e[0],w=e[1]},getOffset:function(){return[ne,se]},moveOffset:function(e){var t=e[0],e=e[1];f+t<0&&(t-=t+f),m+e<0&&(e-=e+m),C<w+e&&(e+=C-(w+e)),y<g+t&&(t+=y-(g+t)),f+=t,g+=t,m+=e,w+=e},getCorner:function(e){var t=Te();switch(e){case"ne":return[t.x2,t.y];case"nw":return[t.x,t.y];case"se":return[t.x2,t.y2];case"sw":return[t.x,t.y2]}},getFixed:Te}),R=(i=!1,n=Me("<div />").css({position:"absolute",zIndex:240,opacity:0}),s={top:xe(),left:xe().height(C),right:xe().height(C),bottom:xe()},{update:ye,updateRaw:Ce,getShades:Ae,setBgColor:_e,enable:ke,disable:Se,resize:function(e,t){s.left.css({height:x(t)}),s.right.css({height:x(t)})},refresh:function(){(S.shade?ke:Se)(),M.isAwake()&&Ie(S.bgOpacity)},opacity:Ie}),M=function(){function e(e,t){t=Me("<div />").mousedown(B(e)).css({cursor:e+"-resize",position:"absolute",zIndex:t}).addClass("ord-"+e);return P.support&&t.bind("touchstart.jcrop",P.createDragger(e)),A.append(t),t}function t(){var e=F.getFixed();F.setPressed([e.x,e.y]),F.setCurrent([e.x2,e.y2]),a()}function a(e){if(l)return o(e)}function o(e){var t,a,o=F.getFixed();t=o.w,a=o.h,T.width(Math.round(t)).height(Math.round(a)),t=o.x,a=o.y,S.shade||I.css({top:x(-a),left:x(-t)}),T.css({top:x(a),left:x(t)}),S.shade&&R.updateRaw(o),l||(T.show(),S.shade?R.opacity(pe):r(pe,!0),l=!0),(e?S.onSelect:S.onChange).call(D,q(o))}function r(e,t,a){(l||t)&&(S.bgFade&&!a?_.animate({opacity:e},{queue:!1,duration:S.fadeTime}):_.css("opacity",e))}function i(){if(c=!0,S.allowResize)return A.show(),!0}function n(){c=!1,A.hide()}function s(e){(e?(te=!0,n):(te=!1,i))()}var l,d=370,c=!1;if(S.dragEdges&&Me.isArray(S.createDragbars))for(var u=S.createDragbars,h=0;h<u.length;h++)u[h],e(u[h],d++).addClass("jcrop-dragbar");if(Me.isArray(S.createHandles))for(var p=S.createHandles,f,m,g=0;g<p.length;g++)p[g],f=p[g],m=void 0,m=S.handleSize,f=e(f,d++).css({opacity:S.handleOpacity}).addClass(k("handle")),m&&f.width(m).height(m),f;if(S.drawBorders&&Me.isArray(S.createBorders))for(var b=S.createBorders,v,w,y=0;y<b.length;y++){switch(b[y]){case"n":v="hline";break;case"s":v="hline bottom";break;case"e":v="vline right";break;case"w":v="vline"}b[y],w=v,w=Me("<div />").css({position:"absolute",opacity:S.borderOpacity}).addClass(k(w)),ue.append(w),w}Me(document).bind("touchstart.jcrop-ios",function(e){Me(e.currentTarget).hasClass("jcrop-tracker")&&e.stopPropagation()});var C=U().mousedown(B("move")).css({cursor:"move",position:"absolute",zIndex:360});return P.support&&C.bind("touchstart.jcrop",P.createDragger("move")),ue.append(C),n(),{updateVisible:a,update:o,release:function(){n(),T.hide(),S.shade?R.opacity(1):r(1),l=!1,S.onRelease.call(D)},refresh:t,isAwake:function(){return l},setCursor:function(e){C.css("cursor",e)},enableHandles:i,enableOnly:function(){c=!0},showHandles:function(){c&&A.show()},disableHandles:n,animMode:s,setBgOpacity:r,done:function(){s(!1),t()}}}(),O=(oe=function(){},re=function(){},(ie=S.trackDocument)||h.mousemove(ge).mouseup(be).mouseout(be),_.before(h),{activateHandlers:function(e,t,a){return o=!0,oe=e,re=t,e=a,h.css({zIndex:450}),e?Me(document).bind("touchmove.jcrop",ve).bind("touchend.jcrop",we):ie&&Me(document).bind("mousemove.jcrop",ge).bind("mouseup.jcrop",be),!1},setCursor:function(e){h.css("cursor",e)}}),fe=(r=Me('<input type="radio" />').css({position:"fixed",left:"-120px",width:"12px"}).addClass("jcrop-keymgr"),ae=Me("<div />").css({position:"absolute",overflow:"hidden"}).append(r),S.keySupport&&(r.keydown(function(e){if(e.ctrlKey||e.metaKey)return!0;var t=!!e.shiftKey?10:1;switch(e.keyCode){case 37:me(e,-t,0);break;case 39:me(e,t,0);break;case 38:me(e,0,-t);break;case 40:me(e,0,t);break;case 27:S.allowSelect&&M.release();break;case 9:return!0}return!1}).blur(function(e){r.hide()}),(le||!S.fixedSupport?(r.css({position:"absolute",left:"-20px"}),ae.append(r)):r).insertBefore(_)),{watchKeys:function(){S.keySupport&&(r.show(),r.focus())}});function me(e,t,a){S.allowMove&&(F.moveOffset([t,a]),M.updateVisible(!0)),e.preventDefault(),e.stopPropagation()}function ge(e){return oe(a(e)),!1}function be(e){return e.preventDefault(),e.stopPropagation(),o&&(o=!1,re(a(e)),M.isAwake()&&S.onSelect.call(D,q(F.getFixed())),h.css({zIndex:290}),Me(document).unbind(".jcrop"),oe=function(){},re=function(){}),!1}function ve(e){return oe(a(P.cfilter(e))),!1}function we(e){return be(P.cfilter(e))}function ye(){return Ce(F.getFixed())}function Ce(e){s.top.css({left:x(e.x),width:x(e.w),height:x(e.y)}),s.bottom.css({top:x(e.y2),left:x(e.x),width:x(e.w),height:x(C-e.y2)}),s.right.css({left:x(e.x2),width:x(y-e.x2)}),s.left.css({width:x(e.x)})}function xe(){return Me("<div />").css({position:"absolute",backgroundColor:S.shadeColor||S.bgColor}).appendTo(n)}function ke(){i||(i=!0,n.insertBefore(_),ye(),M.setBgOpacity(1,0,1),I.hide(),_e(S.shadeColor||S.bgColor,1),M.isAwake()?Ie(S.bgOpacity,1):Ie(1,1))}function _e(e,t){Q(Ae(),e,t)}function Se(){i&&(n.remove(),I.show(),i=!1,M.isAwake()?M.setBgOpacity(S.bgOpacity,1,1):(M.setBgOpacity(1,1,1),M.disableHandles()),Q(c,0,1))}function Ie(e,t){i&&(S.bgFade&&!t?n.animate({opacity:1-e},{queue:!1,duration:S.fadeTime}):n.css({opacity:1-e}))}function Ae(){return n.children()}function Te(){var e,t,a,o,r,i,n,s,l,d,c,u,h;return S.aspectRatio?(t=S.aspectRatio,a=S.minSize[0]/b,o=S.maxSize[0]/b,r=S.maxSize[1]/v,i=g-f,n=w-m,s=Math.abs(i),l=Math.abs(n),0===o&&(o=10*y),0==r&&(r=10*C),s/l<t?(c=w,u=l*t,(d=i<0?f-u:u+f)<0?(d=0,h=Math.abs((d-f)/t),c=n<0?m-h:h+m):y<d&&(d=y,h=Math.abs((d-f)/t),c=n<0?m-h:h+m)):(d=g,h=s/t,(c=n<0?m-h:m+h)<0?(c=0,u=Math.abs((c-m)*t),d=i<0?f-u:u+f):C<c&&(c=C,u=Math.abs(c-m)*t,d=i<0?f-u:u+f)),f<d?(d-f<a?d=f+a:o<d-f&&(d=f+o),c=m<c?m+(d-f)/t:m-(d-f)/t):d<f&&(f-d<a?d=f-a:o<f-d&&(d=f-o),c=m<c?m+(f-d)/t:m-(f-d)/t),d<0?(f-=d,d=0):y<d&&(f-=d-y,d=y),c<0?(m-=c,c=0):C<c&&(m-=c-C,c=C),Fe(Pe(f,m,d,c))):(r=g-f,l=w-m,p&&Math.abs(r)>p&&(g=0<r?f+p:f-p),Z&&Math.abs(l)>Z&&(w=0<l?m+Z:m-Z),ee/v&&Math.abs(l)<ee/v&&(w=0<l?m+ee/v:m-ee/v),$/b&&Math.abs(r)<$/b&&(g=0<r?f+$/b:f-$/b),f<0&&(g-=f,f-=f),m<0&&(w-=m,m-=m),g<0&&(f-=g,g-=g),w<0&&(m-=w,w-=w),y<g&&(f-=e=g-y,g-=e),C<w&&(m-=e=w-C,w-=e),y<f&&(w-=e=f-C,m-=e),C<m&&(w-=e=m-C,m-=e),Fe(Pe(f,m,g,w)))}function ze(e){return e[0]<0&&(e[0]=0),e[1]<0&&(e[1]=0),e[0]>y&&(e[0]=y),e[1]>C&&(e[1]=C),[Math.round(e[0]),Math.round(e[1])]}function Pe(e,t,a,o){var r=e,i=a,n=t,s=o;return a<e&&(r=a,i=e),o<t&&(n=o,s=t),[r,n,i,s]}function Fe(e){return{x:e[0],y:e[1],x2:e[2],y2:e[3],w:e[2]-e[0],h:e[3]-e[1]}}function Re(){var e,t={},a=["touchstart","touchmove","touchend"],o=document.createElement("div");try{for(e=0;e<a.length;e++){var r,i=(r="on"+a[e])in o;i||(o.setAttribute(r,"return;"),i="function"==typeof o[r]),t[a[e]]=i}return t.touchstart&&t.touchend&&t.touchmove}catch(e){return!1}}P.support&&h.bind("touchstart.jcrop",P.newSelection),A.hide(),X(!0);var D={setImage:function(r,i){M.release(),W();var n=new Image;n.onload=function(){var e=n.width,t=n.height,a=S.boxWidth,o=S.boxHeight;_.width(e).height(t),_.attr("src",r),I.attr("src",r),E(_,a,o),y=_.width(),C=_.height(),I.width(y).height(C),h.width(y+2*u).height(C+2*u),c.width(y).height(C),R.resize(y,C),Y(),"function"==typeof i&&i.call(D)},n.src=r},animateTo:function(e,t){function a(){window.setTimeout(h,i)}var o,r,i,n,s,l,d,c,u,h,p=e[0]/b,f=e[1]/v,m=e[2]/b,g=e[3]/v;te||(e=F.flipCoords(p,f,m,g),o=[(o=F.getFixed()).x,o.y,o.x2,o.y2],r=o,i=S.animationDelay,n=e[0]-o[0],s=e[1]-o[1],l=e[2]-o[2],d=e[3]-o[3],c=0,u=S.swingSpeed,p=r[0],f=r[1],m=r[2],g=r[3],M.animMode(!0),h=function(){c+=(100-c)/u,r[0]=Math.round(p+c/100*n),r[1]=Math.round(f+c/100*s),r[2]=Math.round(m+c/100*l),r[3]=Math.round(g+c/100*d),(c=99.8<=c?100:c)<100?(K(r),a()):(M.done(),M.animMode(!1),"function"==typeof t&&t.call(D))},a())},setSelect:G,setOptions:function(e){j(e),X()},tellSelect:function(){return q(F.getFixed())},tellScaled:function(){return F.getFixed()},setClass:function(e){c.removeClass().addClass(k("holder")).addClass(e)},disable:W,enable:Y,cancel:function(){M.done(),O.activateHandlers(null,null)},release:M.release,destroy:function(){c.remove(),d.show(),d.css("visibility","visible"),Me(e).removeData("Jcrop")},focus:fe.watchKeys,getBounds:function(){return[y*b,C*v]},getWidgetSize:function(){return[y,C]},getScaleFactor:function(){return[b,v]},getOptions:function(){return S},ui:{holder:c,selection:T}};return de&&c.bind("selectstart",function(){return!1}),d.data("Jcrop",D),D},Me.fn.Jcrop=function(e,t){var a;return this.each(function(){if(Me(this).data("Jcrop")){if("api"===e)return Me(this).data("Jcrop");Me(this).data("Jcrop").setOptions(e)}else"IMG"==this.tagName?Me.Jcrop.Loader(this,function(){Me(this).css({display:"block",visibility:"hidden"}),a=Me.Jcrop(this,e),Me.isFunction(t)&&t.call(a)}):(Me(this).css({display:"block",visibility:"hidden"}),a=Me.Jcrop(this,e),Me.isFunction(t)&&t.call(a))}),this},Me.Jcrop.Loader=function(e,t,a){var o=Me(e),r=o[0];o.bind("load.jcloader",function e(){r.complete?(o.unbind(".jcloader"),Me.isFunction(t)&&t.call(r)):window.setTimeout(e,50)}).bind("error.jcloader",function(e){o.unbind(".jcloader"),Me.isFunction(a)&&a.call(r)}),r.complete&&Me.isFunction(t)&&(o.unbind(".jcloader"),t.call(r))},Me.Jcrop.defaults={allowSelect:!0,allowMove:!0,allowResize:!0,trackDocument:!0,baseClass:"jcrop",addClass:null,bgColor:"black",bgOpacity:.6,bgFade:!1,borderOpacity:.4,handleOpacity:.5,handleSize:null,aspectRatio:0,keySupport:!0,createHandles:["n","s","e","w","nw","ne","se","sw"],createDragbars:["n","s","e","w"],createBorders:["n","s","e","w"],drawBorders:!0,dragEdges:!0,fixedSupport:!0,touchSupport:null,shade:null,boxWidth:0,boxHeight:0,boundary:2,fadeTime:400,animationDelay:20,swingSpeed:3,minSelect:[0,0],maxSize:[0,0],minSize:[0,0],onChange:function(){},onSelect:function(){},onDblClick:function(){},onRelease:function(){}}},8687:(e,t,a)=>{var u=a(9755),h=a(1692).default;a(1703),a(6647),a(8309),a(2564),function(){var i,a,p,n,r,o,e,t,s,l={version:"2.3.3",name:"jQuery-runner"},d=u;if(!d||!d.fn)throw new Error("["+l.name+"] jQuery or jQuery-like library is required for this plugin to work");function c(e,t,a){var o;if(!(this instanceof c))return new c(e,t,a);this.items=e,o=this.id=r(),this.settings=d.extend({},this.settings,t),n[o]=this,e.each(function(e,t){d(t).data("runner",o)}),this.value(this.settings.startAt),(a||this.settings.autostart)&&this.start()}n={},p=function(e){return(e<10?"0":"")+e},e=1,r=function(){return"runner"+e++},o=(t=this)["r"+(s="equestAnimationFrame")]||t["webkitR"+s]||t["mozR"+s]||t["msR"+s]||function(e){return setTimeout(e,30)},c.prototype.running=!(a=function(e,t){var a,o,r,i,n,s,l,d=["",":",":","."],c=o="",u=(t=t||{}).milliseconds,h=(i=[36e5,6e4,1e3,10]).length;for(e<(n=0)&&(e=Math.abs(e),o="-"),a=s=0,l=i.length;s<l;a=++s)n=0,(r=i[a])<=e&&(e-=(n=Math.floor(e/r))*r),(n||1<a||c)&&(a!==h-1||u)&&(c+=(c?d[a]:"")+p(n));return o+c}),c.prototype.updating=!1,c.prototype.finished=!1,c.prototype.interval=null,c.prototype.total=0,c.prototype.lastTime=0,c.prototype.startTime=0,c.prototype.lastLap=0,c.prototype.lapTime=0,c.prototype.settings={autostart:!1,countdown:!1,stopAt:null,startAt:0,milliseconds:!0,format:null},c.prototype.value=function(a){var o;this.items.each((o=this,function(e,t){t=(e=d(t)).is("input")?"val":"text";e[t](o.format(a))}))},c.prototype.format=function(e){var t=this.settings.format;return(t=d.isFunction(t)?t:a)(e,this.settings)},c.prototype.update=function(){var e,t,a,o;this.updating||(this.updating=!0,t=this.settings,o=d.now(),a=t.stopAt,t=t.countdown,e=o-this.lastTime,this.lastTime=o,t?this.total-=e:this.total+=e,null!==a&&(t&&this.total<=a||!t&&this.total>=a)&&(this.total=a,this.finished=!0,this.stop(),this.fire("runnerFinish")),this.value(this.total),this.updating=!1)},c.prototype.fire=function(e){this.items.trigger(e,this.info())},c.prototype.start=function(){var e,t;this.running||(this.running=!0,this.startTime&&!this.finished||this.reset(),this.lastTime=d.now(),t=this,o(e=function(){t.running&&(t.update(),o(e))}),this.fire("runnerStart"))},c.prototype.stop=function(){this.running&&(this.running=!1,this.update(),this.fire("runnerStop"))},c.prototype.toggle=function(){this.running?this.stop():this.start()},c.prototype.lap=function(){var e=this.lastTime,t=e-this.lapTime;return this.settings.countdown&&(t=-t),(this.running||t)&&(this.lastLap=t,this.lapTime=e),e=this.format(this.lastLap),this.fire("runnerLap"),e},c.prototype.reset=function(e){e&&this.stop(),e=d.now(),"number"!=typeof this.settings.startAt||this.settings.countdown||(e-=this.settings.startAt),this.startTime=this.lapTime=this.lastTime=e,this.total=this.settings.startAt,this.value(this.total),this.finished=!1,this.fire("runnerReset")},c.prototype.info=function(){var e=this.lastLap||0;return{running:this.running,finished:this.finished,time:this.total,formattedTime:this.format(this.total),startTime:this.startTime,lapTime:e,formattedLapTime:this.format(e),settings:this.settings}},i=c,d.fn.runner=function(e,t,a){var o,r;switch("object"===h(e=e||"init")&&(a=t,t=e,e="init"),r=!!(o=this.data("runner"))&&n[o],e){case"init":new i(this,t,a);break;case"info":if(r)return r.info();break;case"reset":r&&r.reset(t);break;case"lap":if(r)return r.lap();break;case"start":case"stop":case"toggle":if(r)return r[e]();break;case"version":return l.version;default:d.error("["+l.name+"] Method "+e+" does not exist")}return this},d.fn.runner.format=a}.call(window)},7604:()=>{tinymce.addI18n("pt_BR",{Redo:"Refazer",Undo:"Desfazer",Cut:"Recortar",Copy:"Copiar",Paste:"Colar","Select all":"Selecionar tudo","New document":"Novo documento",Ok:"Ok",Cancel:"Cancelar","Visual aids":"Ajuda visual",Bold:"Negrito",Italic:"Itálico",Underline:"Sublinhar",Strikethrough:"Riscar",Superscript:"Sobrescrito",Subscript:"Subscrever","Clear formatting":"Limpar formatação","Align left":"Alinhar à esquerda","Align center":"Centralizar","Align right":"Alinhar à direita",Justify:"Justificar","Bullet list":"Lista não ordenada","Numbered list":"Lista ordenada","Decrease indent":"Diminuir recuo","Increase indent":"Aumentar recuo",Close:"Fechar",Formats:"Formatos","Your browser doesn't support direct access to the clipboard. Please use the Ctrl+X/C/V keyboard shortcuts instead.":"Seu navegador não suporta acesso direto à área de transferência. Por favor use os atalhos Ctrl+X - C - V do teclado",Headers:"Cabeçalhos","Header 1":"Cabeçalho 1","Header 2":"Cabeçalho 2","Header 3":"Cabeçalho 3","Header 4":"Cabeçalho 4","Header 5":"Cabeçalho 5","Header 6":"Cabeçalho 6",Headings:"Cabeçalhos","Heading 1":"Cabeçalho 1","Heading 2":"Cabeçalho 2","Heading 3":"Cabeçalho 3","Heading 4":"Cabeçalho 4","Heading 5":"Cabeçalho 5","Heading 6":"Cabeçalho 6",Preformatted:"Preformatado",Div:"Container",Pre:"Pre",Code:"Código",Paragraph:"Parágrafo",Blockquote:"Aspas",Inline:"Em linha",Blocks:"Blocos","Paste is now in plain text mode. Contents will now be pasted as plain text until you toggle this option off.":"O comando colar está agora em modo texto plano. O conteúdo será colado como texto plano até você desligar esta opção.","Font Family":"Fonte","Font Sizes":"Tamanho",Class:"Classe","Browse for an image":"Procure uma imagem",OR:"OU","Drop an image here":"Arraste uma imagem aqui",Upload:"Carregar",Block:"Bloco",Align:"Alinhamento",Default:"Padrão",Circle:"Círculo",Disc:"Disco",Square:"Quadrado","Lower Alpha":"a. b. c. ...","Lower Greek":"α. β. γ. ...","Lower Roman":"i. ii. iii. ...","Upper Alpha":"A. B. C. ...","Upper Roman":"I. II. III. ...",Anchor:"Âncora",Name:"Nome",Id:"Id","Id should start with a letter, followed only by letters, numbers, dashes, dots, colons or underscores.":"Id deve começar com uma letra, seguido apenas por letras, números, traços, pontos, dois pontos ou sublinhados.","You have unsaved changes are you sure you want to navigate away?":"Você tem mudanças não salvas. Você tem certeza que deseja sair?","Restore last draft":"Restaurar último rascunho","Special character":"Caracteres especiais","Source code":"Código fonte","Insert/Edit code sample":"Inserir/Editar código de exemplo",Language:"Idioma","Code sample":"Exemplo de código",Color:"Cor",R:"R",G:"G",B:"B","Left to right":"Da esquerda para a direita","Right to left":"Da direita para a esquerda",Emoticons:"Emoticons","Document properties":"Propriedades do documento",Title:"Título",Keywords:"Palavras-chave",Description:"Descrição",Robots:"Robôs",Author:"Autor",Encoding:"Codificação",Fullscreen:"Tela cheia",Action:"Ação",Shortcut:"Atalho",Help:"Ajuda",Address:"Endereço","Focus to menubar":"Foco no menu","Focus to toolbar":"Foco na barra de ferramentas","Focus to element path":"Foco no caminho do elemento","Focus to contextual toolbar":"Foco na barra de ferramentas contextual","Insert link (if link plugin activated)":"Inserir link (se o plugin de link estiver ativado)","Save (if save plugin activated)":"Salvar (se o plugin de salvar estiver ativado)","Find (if searchreplace plugin activated)":"Procurar (se o plugin de procurar e substituir estiver ativado)","Plugins installed ({0}):":"Plugins instalados ({0}):","Premium plugins:":"Plugins premium:","Learn more...":"Saiba mais...","You are using {0}":"Você está usando {0}",Plugins:"Plugins","Handy Shortcuts":"Atalhos úteis","Horizontal line":"Linha horizontal","Insert/edit image":"Inserir/editar imagem","Image description":"Inserir descrição",Source:"Endereço da imagem",Dimensions:"Dimensões","Constrain proportions":"Manter proporções",General:"Geral",Advanced:"Avançado",Style:"Estilo","Vertical space":"Espaçamento vertical","Horizontal space":"Espaçamento horizontal",Border:"Borda","Insert image":"Inserir imagem",Image:"Imagem","Image list":"Lista de Imagens","Rotate counterclockwise":"Girar em sentido horário","Rotate clockwise":"Girar em sentido anti-horário","Flip vertically":"Virar verticalmente","Flip horizontally":"Virar horizontalmente","Edit image":"Editar imagem","Image options":"Opções de Imagem","Zoom in":"Aumentar zoom","Zoom out":"Diminuir zoom",Crop:"Cortar",Resize:"Redimensionar",Orientation:"Orientação",Brightness:"Brilho",Sharpen:"Aumentar nitidez",Contrast:"Contraste","Color levels":"Níveis de cor",Gamma:"Gama",Invert:"Inverter",Apply:"Aplicar",Back:"Voltar","Insert date/time":"Inserir data/hora","Date/time":"data/hora","Insert link":"Inserir link","Insert/edit link":"Inserir/editar link","Text to display":"Texto para mostrar",Url:"Url",Target:"Alvo",None:"Nenhum","New window":"Nova janela","Remove link":"Remover link",Anchors:"Âncoras",Link:"Link","Paste or type a link":"Cole ou digite um Link","The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?":"The URL you entered seems to be an email address. Do you want to add the required mailto: prefix?","The URL you entered seems to be an external link. Do you want to add the required http:// prefix?":"A URL que você informou parece ser um link externo. Deseja incluir o prefixo http://?","Link list":"Lista de Links","Insert video":"Inserir vídeo","Insert/edit video":"Inserir/editar vídeo","Insert/edit media":"Inserir/editar imagem","Alternative source":"Fonte alternativa",Poster:"Autor","Paste your embed code below:":"Insira o código de incorporação abaixo:",Embed:"Incorporar",Media:"imagem","Nonbreaking space":"Espaço não separável","Page break":"Quebra de página","Paste as text":"Colar como texto",Preview:"Pré-visualizar",Print:"Imprimir",Save:"Salvar",Find:"Localizar","Replace with":"Substituir por",Replace:"Substituir","Replace all":"Substituir tudo",Prev:"Anterior",Next:"Próximo","Find and replace":"Localizar e substituir","Could not find the specified string.":"Não foi possível encontrar o termo especificado","Match case":"Diferenciar maiúsculas e minúsculas","Whole words":"Palavras inteiras",Spellcheck:"Corretor ortográfico",Ignore:"Ignorar","Ignore all":"Ignorar tudo",Finish:"Finalizar","Add to Dictionary":"Adicionar ao Dicionário","Insert table":"Inserir tabela","Table properties":"Propriedades da tabela","Delete table":"Excluir tabela",Cell:"Célula",Row:"Linha",Column:"Coluna","Cell properties":"Propriedades da célula","Merge cells":"Agrupar células","Split cell":"Dividir célula","Insert row before":"Inserir linha antes","Insert row after":"Inserir linha depois","Delete row":"Excluir linha","Row properties":"Propriedades da linha","Cut row":"Recortar linha","Copy row":"Copiar linha","Paste row before":"Colar linha antes","Paste row after":"Colar linha depois","Insert column before":"Inserir coluna antes","Insert column after":"Inserir coluna depois","Delete column":"Excluir coluna",Cols:"Colunas",Rows:"Linhas",Width:"Largura",Height:"Altura","Cell spacing":"Espaçamento da célula","Cell padding":"Espaçamento interno da célula",Caption:"Legenda",Left:"Esquerdo",Center:"Centro",Right:"Direita","Cell type":"Tipo de célula",Scope:"Escopo",Alignment:"Alinhamento","H Align":"Alinhamento H","V Align":"Alinhamento V",Top:"Superior",Middle:"Meio",Bottom:"Inferior","Header cell":"Célula cabeçalho","Row group":"Agrupar linha","Column group":"Agrupar coluna","Row type":"Tipo de linha",Header:"Cabeçalho",Body:"Corpo",Footer:"Rodapé","Border color":"Cor da borda","Insert template":"Inserir modelo",Templates:"Modelos",Template:"Modelo","Text color":"Cor do texto","Background color":"Cor do fundo","Custom...":"Personalizado...","Custom color":"Cor personalizada","No color":"Nenhuma cor","Table of Contents":"índice de Conteúdo","Show blocks":"Mostrar blocos","Show invisible characters":"Exibir caracteres invisíveis","Words: {0}":"Palavras: {0}","{0} words":"{0} palavras",File:"Arquivo",Edit:"Editar",Insert:"Inserir",View:"Visualizar",Format:"Formatar",Table:"Tabela",Tools:"Ferramentas","Powered by {0}":"Distribuído por  {0}","Rich Text Area. Press ALT-F9 for menu. Press ALT-F10 for toolbar. Press ALT-0 for help":"Área de texto formatado. Pressione ALT-F9 para exibir o menu, ALT-F10 para exibir a barra de ferramentas ou ALT-0 para exibir a ajuda"})},1855:(e,t,a)=>{"use strict";a(6992),a(8674),a(9601),a(7727),a(3734),a(6688),a(5476),a(2466),a(2526),a(4414),a(2993),a(13);var o=a(381),r=(a(7971),a(7575)),r=a.n(r),r=(a(8860),a(6890),a(7490),a(8190),a(4400),a(2682),a(6552),a(8619),a(7604),window.tinymce=r(),window.initTextRichEditor=function(e){var t=1<arguments.length&&void 0!==arguments[1]&&arguments[1],e={selector:null==e?"textarea":e,language:"pt_BR",branding:!1,forced_root_block:"p",paste_as_text:2<arguments.length&&void 0!==arguments[2]&&arguments[2],plugins:"table lists advlist link code",toolbar:"undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link | code",menubar:"file edit view insert format table"};t&&(e.readonly=1,e.menubar=!1,e.toolbar=!1),window.tinymce.init(e)},a(4730),a(4124),a(5228),a(8687),a(9755));a(9755),window.$=r;window.moment=o,window.autorModal(),window.refreshMask(),window.refreshDatePicker(),window.initTextRichEditor("#texto-rico")},4391:(e,t,a)=>{var o={"./pt-br":7971,"./pt-br.js":7971,"moment/locale/pt-br":7971,"moment/locale/pt-br.js":7971};function r(e){e=i(e);return a(e)}function i(e){if(a.o(o,e))return o[e];throw(e=new Error("Cannot find module '"+e+"'")).code="MODULE_NOT_FOUND",e}r.keys=function(){return Object.keys(o)},r.resolve=i,(e.exports=r).id=4391}},o={};function u(e){var t=o[e];return void 0!==t||(t=o[e]={id:e,loaded:!1,exports:{}},a[e].call(t.exports,t,t.exports,u),t.loaded=!0),t.exports}u.m=a,d=[],u.O=(e,t,a,o)=>{if(!t){for(var r=1/0,i=0;i<d.length;i++){for(var n,[t,a,o]=d[i],s=!0,l=0;l<t.length;l++)(!1&o||o<=r)&&Object.keys(u.O).every(e=>u.O[e](t[l]))?t.splice(l--,1):(s=!1,o<r&&(r=o));s&&(d.splice(i--,1),void 0!==(n=a()))&&(e=n)}return e}o=o||0;for(var i=d.length;0<i&&d[i-1][2]>o;i--)d[i]=d[i-1];d[i]=[t,a,o]},u.n=e=>{var t=e&&e.__esModule?()=>e.default:()=>e;return u.d(t,{a:t}),t},u.d=(e,t)=>{for(var a in t)u.o(t,a)&&!u.o(e,a)&&Object.defineProperty(e,a,{enumerable:!0,get:t[a]})},u.g=function(){if("object"==typeof globalThis)return globalThis;try{return this||new Function("return this")()}catch(e){if("object"==typeof window)return window}}(),u.o=(e,t)=>Object.prototype.hasOwnProperty.call(e,t),u.r=e=>{"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},u.nmd=e=>(e.paths=[],e.children||(e.children=[]),e),u.j=172,c={172:0},u.O.j=e=>0===c[e],t=(e,t)=>{var a,o,r,[i,n,s]=t,l=0;if(i.some(e=>0!==c[e])){for(a in n)u.o(n,a)&&(u.m[a]=n[a]);s&&(r=s(u))}for(e&&e(t);l<i.length;l++)o=i[l],u.o(c,o)&&c[o]&&c[o][0](),c[o]=0;return u.O(r)},(e=self.webpackChunksapl_frontend=self.webpackChunksapl_frontend||[]).forEach(t.bind(null,0)),e.push=t.bind(null,e.push.bind(e));var t=u.O(void 0,[998],()=>u(1855));u.O(t)})();