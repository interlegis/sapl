!function(e){function t(t){for(var r,o,s=t[0],i=t[1],u=t[2],l=0,f=[];l<s.length;l++)o=s[l],Object.prototype.hasOwnProperty.call(a,o)&&a[o]&&f.push(a[o][0]),a[o]=0;for(r in i)Object.prototype.hasOwnProperty.call(i,r)&&(e[r]=i[r]);for(d&&d(t);f.length;)f.shift()();return c.push.apply(c,u||[]),n()}function n(){for(var e,t=0;t<c.length;t++){for(var n=c[t],r=!0,o=1;o<n.length;o++){var i=n[o];0!==a[i]&&(r=!1)}r&&(c.splice(t--,1),e=s(s.s=n[0]))}return e}var r={},o={online:0},a={online:0},c=[];function s(t){if(r[t])return r[t].exports;var n=r[t]={i:t,l:!1,exports:{}};return e[t].call(n.exports,n,n.exports,s),n.l=!0,n.exports}s.e=function(e){var t=[];o[e]?t.push(o[e]):0!==o[e]&&{"chunk-09995afe":1,"chunk-31d76f93":1,"chunk-681dd124":1}[e]&&t.push(o[e]=new Promise((function(t,n){for(var r="css/"+({}[e]||e)+"."+{"chunk-09995afe":"a646904b","chunk-2d0c4a82":"31d6cfe0","chunk-2d0e8be2":"31d6cfe0","chunk-31d76f93":"7e9bcf20","chunk-681dd124":"34410740"}[e]+".css",a=s.p+r,c=document.getElementsByTagName("link"),i=0;i<c.length;i++){var u=(d=c[i]).getAttribute("data-href")||d.getAttribute("href");if("stylesheet"===d.rel&&(u===r||u===a))return t()}var l=document.getElementsByTagName("style");for(i=0;i<l.length;i++){var d;if((u=(d=l[i]).getAttribute("data-href"))===r||u===a)return t()}var f=document.createElement("link");f.rel="stylesheet",f.type="text/css",f.onload=t,f.onerror=function(t){var r=t&&t.target&&t.target.src||a,c=new Error("Loading CSS chunk "+e+" failed.\n("+r+")");c.code="CSS_CHUNK_LOAD_FAILED",c.request=r,delete o[e],f.parentNode.removeChild(f),n(c)},f.href=a,document.getElementsByTagName("head")[0].appendChild(f)})).then((function(){o[e]=0})));var n=a[e];if(0!==n)if(n)t.push(n[2]);else{var r=new Promise((function(t,r){n=a[e]=[t,r]}));t.push(n[2]=r);var c,i=document.createElement("script");i.charset="utf-8",i.timeout=120,s.nc&&i.setAttribute("nonce",s.nc),i.src=function(e){return s.p+"js/"+({}[e]||e)+"."+{"chunk-09995afe":"a6f4abba","chunk-2d0c4a82":"75cb4df5","chunk-2d0e8be2":"d53f5a24","chunk-31d76f93":"fb085f5d","chunk-681dd124":"b923be8d"}[e]+".js"}(e);var u=new Error;c=function(t){i.onerror=i.onload=null,clearTimeout(l);var n=a[e];if(0!==n){if(n){var r=t&&("load"===t.type?"missing":t.type),o=t&&t.target&&t.target.src;u.message="Loading chunk "+e+" failed.\n("+r+": "+o+")",u.name="ChunkLoadError",u.type=r,u.request=o,n[1](u)}a[e]=void 0}};var l=setTimeout((function(){c({type:"timeout",target:i})}),12e4);i.onerror=i.onload=c,document.head.appendChild(i)}return Promise.all(t)},s.m=e,s.c=r,s.d=function(e,t,n){s.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:n})},s.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},s.t=function(e,t){if(1&t&&(e=s(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var n=Object.create(null);if(s.r(n),Object.defineProperty(n,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var r in e)s.d(n,r,function(t){return e[t]}.bind(null,r));return n},s.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return s.d(t,"a",t),t},s.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},s.p="/static/sapl/frontend/",s.oe=function(e){throw console.error(e),e};var i=window.webpackJsonp=window.webpackJsonp||[],u=i.push.bind(i);i.push=t,i=i.slice();for(var l=0;l<i.length;l++)t(i[l]);var d=u;c.push([3,"chunk-vendors"]),n()}({"0b78":function(e,t,n){},3:function(e,t,n){e.exports=n("56d7")},"56d7":function(e,t,n){"use strict";n.r(t);n("cadf"),n("551c"),n("f751"),n("097d");var r,o=n("a026"),a=n("2f62"),c=n("5f5b"),s=n("b408"),i=n.n(s),u=n("8c4f"),l=n("a430"),d=n("bd86"),f=n("975e"),p=(r={},Object(d.a)(r,"REMOVE_FROM_STATE",(function(e,t){var n=t.message;e.cache.hasOwnProperty(n.app)&&e.cache[n.app].hasOwnProperty(n.model)&&e.cache[n.app][n.model][n.id]&&delete e.cache[n.app][n.model][n.id]})),Object(d.a)(r,"INSERT_IN_STATE",(function(e,t){e.cache.hasOwnProperty(t.app)||(e.cache[t.app]={}),e.cache[t.app].hasOwnProperty(t.model)||(e.cache[t.app][t.model]={}),e.cache[t.app][t.model][t.id]=t.value})),r),h={state:{cache:{}},mutations:p,getters:{getModel:function(e){return function(t){return e.cache.hasOwnProperty(t.app)&&e.cache[t.app].hasOwnProperty(t.model)&&e.cache[t.app][t.model].hasOwnProperty(t.id)?e.cache[t.app][t.model]:null}}},actions:{removeFromState:function(e,t){return(0,e.commit)("REMOVE_FROM_STATE",t)},insertInState:function(e,t){var n=e.commit,r=e.getters;if(!t.hasOwnProperty("value")){var o=function(){return f.a.Utils.getModel(t.app,t.model,t.id).then((function(e){n("INSERT_IN_STATE",{app:t.app,model:t.model,value:e.data,id:e.data.id})})).catch((function(e){return t.component.sendMessage({alert:"danger",message:"Não foi possível fetch...",time:5})}))},a=r.getModel(t);return null===a?(n("INSERT_IN_STATE",t),o()):a.hasOwnProperty(t.id)?void 0:o()}n("INSERT_IN_STATE",t)}}},m={modules:{store__message:l.a,store__online:h},strict:!0},g=n("bc3a"),b=n.n(g),O=n("31bd"),v=n("cd4e"),y=(n("ed27"),[{path:"/online",component:function(){return n.e("chunk-681dd124").then(n.bind(null,"1579"))},children:[{path:"",name:"index_link",component:function(){return n.e("chunk-2d0e8be2").then(n.bind(null,"8b24"))}},{path:"sessao/",name:"sessao_link",component:function(){return n.e("chunk-2d0c4a82").then(n.bind(null,"3c84"))},children:[{path:"list/",name:"sessao_list_link",component:function(){return n.e("chunk-31d76f93").then(n.bind(null,"d92f"))}},{path:":id/",name:"sessao_plenaria_online_link",component:function(){return n.e("chunk-09995afe").then(n.bind(null,"4a7e"))}}]}]}]);n("8e6e"),n("ac6a"),n("456d");function w(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function j(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?w(n,!0).forEach((function(t){Object(d.a)(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):w(n).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}var _={name:"alert",extends:j({},n("5fda").default),props:["message_id","show"],data:function(){return{}},watch:{show:function(e,t){e<=1&&this.popMessage(this.message_id)}},methods:j({},Object(a.b)(["popMessage"]))},P=n("0c7c"),k=Object(P.a)(_,void 0,void 0,!1,null,"067e5642",null).exports;function E(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}var S={name:"message",data:function(){return{}},computed:function(e){for(var t=1;t<arguments.length;t++){var n=null!=arguments[t]?arguments[t]:{};t%2?E(n,!0).forEach((function(t){Object(d.a)(e,t,n[t])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(n)):E(n).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(n,t))}))}return e}({},Object(a.c)({getMessages:"getMessages"})),components:{alert:k}},T=(n("eb0d"),Object(P.a)(S,(function(){var e=this,t=e.$createElement,n=e._self._c||t;return n("div",{staticClass:"container-messages"},e._l(e.getMessages,(function(t,r){return n("alert",{key:r,attrs:{variant:t.alert,show:"",dismissible:"",message_id:t.id},model:{value:t.time,callback:function(n){e.$set(t,"time",n)},expression:"msg.time"}},[e._v("\n      "+e._s(t.message)+"\n  ")])})),1)}),[],!1,null,"26b3e554",null).exports),M=n("81f6"),x={name:"app",components:{Message:T},mounted:function(){var e=this;this.$options.sockets.onmessage=function(t){var n=JSON.parse(t.data);e.sendMessage({alert:"info",message:"Base Atualizada",time:3}),e.removeFromState(n),M.a.$emit("ws-message",n)}}},A=Object(P.a)(x,(function(){var e=this.$createElement,t=this._self._c||e;return t("div",{attrs:{id:"app-frontend-base-content"}},[t("message"),t("router-view")],1)}),[],!1,null,null,null).exports;n("9c9e");b.a.defaults.xsrfCookieName="csrftoken",b.a.defaults.xsrfHeaderName="X-CSRFToken",o.default.use(a.a),o.default.use(u.a),o.default.use(c.a),o.default.use(i.a,("https:"===window.location.protocol?"wss://":"ws://")+window.location.host+"/ws/time-refresh/",{reconnection:!0}),Object(v.loadProgressBar)(),o.default.config.productionTip=!1;var N=new a.a.Store(m),D=new u.a({routes:y,mode:"history"});Object(O.sync)(N,D);new o.default({router:D,store:N,el:"#app-frontend-base-content",components:{App:A},template:"<App/>"})},"81f6":function(e,t,n){"use strict";n.d(t,"a",(function(){return r}));var r=new(n("a026").default)},"975e":function(e,t,n){"use strict";var r=n("bc3a"),o=n.n(r);o.a.defaults.xsrfCookieName="csrftoken",o.a.defaults.xsrfHeaderName="X-CSRFToken",t.a={Utils:{getYearsChoiceList:function(e,t){return o()({url:"".concat("/api","/").concat(e,"/").concat(t,"/years"),method:"GET"})},getModelOrderedList:function(e,t){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:"",r=arguments.length>3&&void 0!==arguments[3]?arguments[3]:1,a=arguments.length>4&&void 0!==arguments[4]?arguments[4]:"";return o()({url:"".concat("/api","/").concat(e,"/").concat(t,"/?o=").concat(n,"&page=").concat(r).concat(a),method:"GET"})},getModelList:function(e,t){var n=arguments.length>2&&void 0!==arguments[2]?arguments[2]:1;return o()({url:"".concat("/api","/").concat(e,"/").concat(t,"/?page=").concat(n),method:"GET"})},getModel:function(e,t,n){return o()({url:"".concat("/api","/").concat(e,"/").concat(t,"/").concat(n),method:"GET"})}}}},"9c9e":function(e,t,n){"use strict";(function(e){n("8e6e"),n("ac6a"),n("456d"),n("28a5");var t=n("bd86"),r=n("a026"),o=n("2f62"),a=n("81f6");function c(e,t){var n=Object.keys(e);if(Object.getOwnPropertySymbols){var r=Object.getOwnPropertySymbols(e);t&&(r=r.filter((function(t){return Object.getOwnPropertyDescriptor(e,t).enumerable}))),n.push.apply(n,r)}return n}function s(e){for(var n=1;n<arguments.length;n++){var r=null!=arguments[n]?arguments[n]:{};n%2?c(r,!0).forEach((function(n){Object(t.a)(e,n,r[n])})):Object.getOwnPropertyDescriptors?Object.defineProperties(e,Object.getOwnPropertyDescriptors(r)):c(r).forEach((function(t){Object.defineProperty(e,t,Object.getOwnPropertyDescriptor(r,t))}))}return e}r.default.use(o.a),r.default.mixin({computed:s({},o.a.mapGetters(["getModel"])),methods:s({},o.a.mapActions(["sendMessage","removeFromState","insertInState"]),{stringToDate:function(e,t,n){var r=t.toLowerCase().split(n),o=e.split(n),a=r.indexOf("mm"),c=r.indexOf("dd"),s=r.indexOf("yyyy"),i=parseInt(o[a]);return i-=1,new Date(o[s],i,o[c])},on_ws_message:function(t){this.hasOwnProperty("app")&&this.hasOwnProperty("model")&&(Array.isArray(this.app)&&Array.isArray(this.model)?-1!==e.indexOf(this.app,t.message.app)&&-1!==e.indexOf(this.model,t.message.model)&&this.fetch():t.message.app===this.app&&t.message.model===this.model&&this.fetch())}}),created:function(){a.a.$on("ws-message",this.on_ws_message)}})}).call(this,n("2ef0"))},a430:function(e,t,n){"use strict";(function(e){var r,o=n("bd86"),a=n("d8e2"),c=(r={},Object(o.a)(r,a.b,(function(e,t){t.id=e.counter_id++,e.messages.unshift(t)})),Object(o.a)(r,a.a,(function(t,n){e.remove(t.messages,(function(e){return n===e.id}))})),r),s={sendMessage:function(e,t){return(0,e.commit)(a.b,t)},popMessage:function(e,t){return(0,e.commit)(a.a,t)}};t.a={state:{messages:[],counter_id:0},mutations:c,getters:{getMessages:function(e){return e.messages}},actions:s}}).call(this,n("2ef0"))},d8e2:function(e,t,n){"use strict";n.d(t,"b",(function(){return r})),n.d(t,"a",(function(){return o}));var r="MESSAGE_SHIFT",o="MESSAGE_POP"},eb0d:function(e,t,n){"use strict";var r=n("0b78");n.n(r).a}});