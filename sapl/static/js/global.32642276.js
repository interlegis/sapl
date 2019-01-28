/******/ (function(modules) { // webpackBootstrap
/******/ 	// install a JSONP callback for chunk loading
/******/ 	function webpackJsonpCallback(data) {
/******/ 		var chunkIds = data[0];
/******/ 		var moreModules = data[1];
/******/ 		var executeModules = data[2];
/******/
/******/ 		// add "moreModules" to the modules object,
/******/ 		// then flag all "chunkIds" as loaded and fire callback
/******/ 		var moduleId, chunkId, i = 0, resolves = [];
/******/ 		for(;i < chunkIds.length; i++) {
/******/ 			chunkId = chunkIds[i];
/******/ 			if(installedChunks[chunkId]) {
/******/ 				resolves.push(installedChunks[chunkId][0]);
/******/ 			}
/******/ 			installedChunks[chunkId] = 0;
/******/ 		}
/******/ 		for(moduleId in moreModules) {
/******/ 			if(Object.prototype.hasOwnProperty.call(moreModules, moduleId)) {
/******/ 				modules[moduleId] = moreModules[moduleId];
/******/ 			}
/******/ 		}
/******/ 		if(parentJsonpFunction) parentJsonpFunction(data);
/******/
/******/ 		while(resolves.length) {
/******/ 			resolves.shift()();
/******/ 		}
/******/
/******/ 		// add entry modules from loaded chunk to deferred list
/******/ 		deferredModules.push.apply(deferredModules, executeModules || []);
/******/
/******/ 		// run deferred modules when all chunks ready
/******/ 		return checkDeferredModules();
/******/ 	};
/******/ 	function checkDeferredModules() {
/******/ 		var result;
/******/ 		for(var i = 0; i < deferredModules.length; i++) {
/******/ 			var deferredModule = deferredModules[i];
/******/ 			var fulfilled = true;
/******/ 			for(var j = 1; j < deferredModule.length; j++) {
/******/ 				var depId = deferredModule[j];
/******/ 				if(installedChunks[depId] !== 0) fulfilled = false;
/******/ 			}
/******/ 			if(fulfilled) {
/******/ 				deferredModules.splice(i--, 1);
/******/ 				result = __webpack_require__(__webpack_require__.s = deferredModule[0]);
/******/ 			}
/******/ 		}
/******/ 		return result;
/******/ 	}
/******/
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// object to store loaded CSS chunks
/******/ 	var installedCssChunks = {
/******/ 		"global": 0
/******/ 	}
/******/
/******/ 	// object to store loaded and loading chunks
/******/ 	// undefined = chunk not loaded, null = chunk preloaded/prefetched
/******/ 	// Promise = chunk loading, 0 = chunk loaded
/******/ 	var installedChunks = {
/******/ 		"global": 0
/******/ 	};
/******/
/******/ 	var deferredModules = [];
/******/
/******/ 	// script path function
/******/ 	function jsonpScriptSrc(chunkId) {
/******/ 		return __webpack_require__.p + "js/" + ({"image_cropping":"image_cropping","jquery_mask_plugin":"jquery_mask_plugin"}[chunkId]||chunkId) + "." + {"image_cropping":"c0e3598f","jquery_mask_plugin":"8c657459"}[chunkId] + ".js"
/******/ 	}
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId]) {
/******/ 			return installedModules[moduleId].exports;
/******/ 		}
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			i: moduleId,
/******/ 			l: false,
/******/ 			exports: {}
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.l = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/ 	// This file contains only the entry chunk.
/******/ 	// The chunk loading function for additional chunks
/******/ 	__webpack_require__.e = function requireEnsure(chunkId) {
/******/ 		var promises = [];
/******/
/******/
/******/ 		// mini-css-extract-plugin CSS loading
/******/ 		var cssChunks = {"image_cropping":1};
/******/ 		if(installedCssChunks[chunkId]) promises.push(installedCssChunks[chunkId]);
/******/ 		else if(installedCssChunks[chunkId] !== 0 && cssChunks[chunkId]) {
/******/ 			promises.push(installedCssChunks[chunkId] = new Promise(function(resolve, reject) {
/******/ 				var href = "css/" + ({"image_cropping":"image_cropping","jquery_mask_plugin":"jquery_mask_plugin"}[chunkId]||chunkId) + "." + {"image_cropping":"8608d5e7","jquery_mask_plugin":"31d6cfe0"}[chunkId] + ".css";
/******/ 				var fullhref = __webpack_require__.p + href;
/******/ 				var existingLinkTags = document.getElementsByTagName("link");
/******/ 				for(var i = 0; i < existingLinkTags.length; i++) {
/******/ 					var tag = existingLinkTags[i];
/******/ 					var dataHref = tag.getAttribute("data-href") || tag.getAttribute("href");
/******/ 					if(tag.rel === "stylesheet" && (dataHref === href || dataHref === fullhref)) return resolve();
/******/ 				}
/******/ 				var existingStyleTags = document.getElementsByTagName("style");
/******/ 				for(var i = 0; i < existingStyleTags.length; i++) {
/******/ 					var tag = existingStyleTags[i];
/******/ 					var dataHref = tag.getAttribute("data-href");
/******/ 					if(dataHref === href || dataHref === fullhref) return resolve();
/******/ 				}
/******/ 				var linkTag = document.createElement("link");
/******/ 				linkTag.rel = "stylesheet";
/******/ 				linkTag.type = "text/css";
/******/ 				linkTag.onload = resolve;
/******/ 				linkTag.onerror = function(event) {
/******/ 					var request = event && event.target && event.target.src || fullhref;
/******/ 					var err = new Error("Loading CSS chunk " + chunkId + " failed.\n(" + request + ")");
/******/ 					err.request = request;
/******/ 					delete installedCssChunks[chunkId]
/******/ 					linkTag.parentNode.removeChild(linkTag)
/******/ 					reject(err);
/******/ 				};
/******/ 				linkTag.href = fullhref;
/******/
/******/ 				var head = document.getElementsByTagName("head")[0];
/******/ 				head.appendChild(linkTag);
/******/ 			}).then(function() {
/******/ 				installedCssChunks[chunkId] = 0;
/******/ 			}));
/******/ 		}
/******/
/******/ 		// JSONP chunk loading for javascript
/******/
/******/ 		var installedChunkData = installedChunks[chunkId];
/******/ 		if(installedChunkData !== 0) { // 0 means "already installed".
/******/
/******/ 			// a Promise means "currently loading".
/******/ 			if(installedChunkData) {
/******/ 				promises.push(installedChunkData[2]);
/******/ 			} else {
/******/ 				// setup Promise in chunk cache
/******/ 				var promise = new Promise(function(resolve, reject) {
/******/ 					installedChunkData = installedChunks[chunkId] = [resolve, reject];
/******/ 				});
/******/ 				promises.push(installedChunkData[2] = promise);
/******/
/******/ 				// start chunk loading
/******/ 				var script = document.createElement('script');
/******/ 				var onScriptComplete;
/******/
/******/ 				script.charset = 'utf-8';
/******/ 				script.timeout = 120;
/******/ 				if (__webpack_require__.nc) {
/******/ 					script.setAttribute("nonce", __webpack_require__.nc);
/******/ 				}
/******/ 				script.src = jsonpScriptSrc(chunkId);
/******/
/******/ 				onScriptComplete = function (event) {
/******/ 					// avoid mem leaks in IE.
/******/ 					script.onerror = script.onload = null;
/******/ 					clearTimeout(timeout);
/******/ 					var chunk = installedChunks[chunkId];
/******/ 					if(chunk !== 0) {
/******/ 						if(chunk) {
/******/ 							var errorType = event && (event.type === 'load' ? 'missing' : event.type);
/******/ 							var realSrc = event && event.target && event.target.src;
/******/ 							var error = new Error('Loading chunk ' + chunkId + ' failed.\n(' + errorType + ': ' + realSrc + ')');
/******/ 							error.type = errorType;
/******/ 							error.request = realSrc;
/******/ 							chunk[1](error);
/******/ 						}
/******/ 						installedChunks[chunkId] = undefined;
/******/ 					}
/******/ 				};
/******/ 				var timeout = setTimeout(function(){
/******/ 					onScriptComplete({ type: 'timeout', target: script });
/******/ 				}, 120000);
/******/ 				script.onerror = script.onload = onScriptComplete;
/******/ 				document.head.appendChild(script);
/******/ 			}
/******/ 		}
/******/ 		return Promise.all(promises);
/******/ 	};
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// define getter function for harmony exports
/******/ 	__webpack_require__.d = function(exports, name, getter) {
/******/ 		if(!__webpack_require__.o(exports, name)) {
/******/ 			Object.defineProperty(exports, name, { enumerable: true, get: getter });
/******/ 		}
/******/ 	};
/******/
/******/ 	// define __esModule on exports
/******/ 	__webpack_require__.r = function(exports) {
/******/ 		if(typeof Symbol !== 'undefined' && Symbol.toStringTag) {
/******/ 			Object.defineProperty(exports, Symbol.toStringTag, { value: 'Module' });
/******/ 		}
/******/ 		Object.defineProperty(exports, '__esModule', { value: true });
/******/ 	};
/******/
/******/ 	// create a fake namespace object
/******/ 	// mode & 1: value is a module id, require it
/******/ 	// mode & 2: merge all properties of value into the ns
/******/ 	// mode & 4: return value when already ns object
/******/ 	// mode & 8|1: behave like require
/******/ 	__webpack_require__.t = function(value, mode) {
/******/ 		if(mode & 1) value = __webpack_require__(value);
/******/ 		if(mode & 8) return value;
/******/ 		if((mode & 4) && typeof value === 'object' && value && value.__esModule) return value;
/******/ 		var ns = Object.create(null);
/******/ 		__webpack_require__.r(ns);
/******/ 		Object.defineProperty(ns, 'default', { enumerable: true, value: value });
/******/ 		if(mode & 2 && typeof value != 'string') for(var key in value) __webpack_require__.d(ns, key, function(key) { return value[key]; }.bind(null, key));
/******/ 		return ns;
/******/ 	};
/******/
/******/ 	// getDefaultExport function for compatibility with non-harmony modules
/******/ 	__webpack_require__.n = function(module) {
/******/ 		var getter = module && module.__esModule ?
/******/ 			function getDefault() { return module['default']; } :
/******/ 			function getModuleExports() { return module; };
/******/ 		__webpack_require__.d(getter, 'a', getter);
/******/ 		return getter;
/******/ 	};
/******/
/******/ 	// Object.prototype.hasOwnProperty.call
/******/ 	__webpack_require__.o = function(object, property) { return Object.prototype.hasOwnProperty.call(object, property); };
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "/static/";
/******/
/******/ 	// on error function for async loading
/******/ 	__webpack_require__.oe = function(err) { console.error(err); throw err; };
/******/
/******/ 	var jsonpArray = window["webpackJsonp"] = window["webpackJsonp"] || [];
/******/ 	var oldJsonpFunction = jsonpArray.push.bind(jsonpArray);
/******/ 	jsonpArray.push = webpackJsonpCallback;
/******/ 	jsonpArray = jsonpArray.slice();
/******/ 	for(var i = 0; i < jsonpArray.length; i++) webpackJsonpCallback(jsonpArray[i]);
/******/ 	var parentJsonpFunction = oldJsonpFunction;
/******/
/******/
/******/ 	// add entry module to deferred list
/******/ 	deferredModules.push([1,"chunk-vendors"]);
/******/ 	// run deferred modules when ready
/******/ 	return checkDeferredModules();
/******/ })
/************************************************************************/
/******/ ({

/***/ "0afa":
/*!****************************!*\
  !*** ./src/global/main.js ***!
  \****************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* harmony import */ var core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! core-js/modules/es6.array.iterator */ \"cadf\");\n/* harmony import */ var core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! core-js/modules/es6.promise */ \"551c\");\n/* harmony import */ var core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! core-js/modules/es7.promise.finally */ \"097d\");\n/* harmony import */ var core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var bootstrap__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! bootstrap */ \"4989\");\n/* harmony import */ var bootstrap__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(bootstrap__WEBPACK_IMPORTED_MODULE_3__);\n/* harmony import */ var webpack_jquery_ui_dialog__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! webpack-jquery-ui/dialog */ \"cb1e\");\n/* harmony import */ var webpack_jquery_ui_dialog__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(webpack_jquery_ui_dialog__WEBPACK_IMPORTED_MODULE_4__);\n/* harmony import */ var webpack_jquery_ui_sortable__WEBPACK_IMPORTED_MODULE_5__ = __webpack_require__(/*! webpack-jquery-ui/sortable */ \"8501\");\n/* harmony import */ var webpack_jquery_ui_sortable__WEBPACK_IMPORTED_MODULE_5___default = /*#__PURE__*/__webpack_require__.n(webpack_jquery_ui_sortable__WEBPACK_IMPORTED_MODULE_5__);\n/* harmony import */ var _functions__WEBPACK_IMPORTED_MODULE_6__ = __webpack_require__(/*! ./functions */ \"4e1f\");\n\n\n\n\n\n\n\n__webpack_require__.e(/*! import() | jquery_mask_plugin */ \"jquery_mask_plugin\").then(__webpack_require__.t.bind(null, /*! jquery-mask-plugin */ \"6bd7\", 7)).then(function (jquery_mask_plugin) {\n  jquery_mask_plugin.default();\n});\n__webpack_require__.e(/*! import() | image_cropping */ \"image_cropping\").then(__webpack_require__.bind(null, /*! ./image_cropping */ \"1b23\")).then(function (image_cropping) {\n  image_cropping.default();\n}); // eslint-disable-next-line\n\n__webpack_require__(/*! imports-loader?window.jQuery=jquery!./jquery.runner.js */ \"59ca\");\n\nwindow.autorModal();\nwindow.refreshMask(); // \"sapl-oficial-theme\": \"../../sapl-oficial-theme\",//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiMGFmYS5qcyIsInNvdXJjZXMiOlsid2VicGFjazovLy8uL3NyYy9nbG9iYWwvbWFpbi5qcz8wYWZhIl0sInNvdXJjZXNDb250ZW50IjpbImltcG9ydCAnYm9vdHN0cmFwJ1xuXG5pbXBvcnQgJ3dlYnBhY2stanF1ZXJ5LXVpL2RpYWxvZydcbmltcG9ydCAnd2VicGFjay1qcXVlcnktdWkvc29ydGFibGUnXG5cbmltcG9ydCAnLi9mdW5jdGlvbnMnXG5cbmltcG9ydChcbiAgLyogd2VicGFja0NodW5rTmFtZTogXCJqcXVlcnlfbWFza19wbHVnaW5cIiAqL1xuICAnanF1ZXJ5LW1hc2stcGx1Z2luJylcbiAgLnRoZW4oanF1ZXJ5X21hc2tfcGx1Z2luID0+IHtcbiAgICBqcXVlcnlfbWFza19wbHVnaW4uZGVmYXVsdCgpXG4gIH0pXG5cbmltcG9ydChcbiAgLyogd2VicGFja0NodW5rTmFtZTogXCJpbWFnZV9jcm9wcGluZ1wiICovXG4gICcuL2ltYWdlX2Nyb3BwaW5nJylcbiAgLnRoZW4oaW1hZ2VfY3JvcHBpbmcgPT4ge1xuICAgIGltYWdlX2Nyb3BwaW5nLmRlZmF1bHQoKVxuICB9KVxuXG4vLyBlc2xpbnQtZGlzYWJsZS1uZXh0LWxpbmVcbnJlcXVpcmUoJ2ltcG9ydHMtbG9hZGVyP3dpbmRvdy5qUXVlcnk9anF1ZXJ5IS4vanF1ZXJ5LnJ1bm5lci5qcycpXG5cbndpbmRvdy5hdXRvck1vZGFsKClcbndpbmRvdy5yZWZyZXNoTWFzaygpXG5cbi8vIFwic2FwbC1vZmljaWFsLXRoZW1lXCI6IFwiLi4vLi4vc2FwbC1vZmljaWFsLXRoZW1lXCIsXG4iXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQUE7QUFFQTtBQUNBO0FBRUE7QUFFQSw0SkFFQTtBQUVBO0FBQ0E7QUFFQSw2SUFFQTtBQUVBO0FBQ0E7QUFDQTtBQUVBO0FBQ0E7QUFDQTtBQUNBIiwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///0afa\n");

/***/ }),

/***/ 1:
/*!**********************************!*\
  !*** multi ./src/global/main.js ***!
  \**********************************/
/*! no static exports found */
/***/ (function(module, exports, __webpack_require__) {

module.exports = __webpack_require__(/*! ./src/global/main.js */"0afa");


/***/ }),

/***/ "4e1f":
/*!*********************************!*\
  !*** ./src/global/functions.js ***!
  \*********************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* WEBPACK VAR INJECTION */(function(jQuery, __webpack_provided_window_dot_jQuery, $) {/* harmony import */ var core_js_modules_web_dom_iterable__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! core-js/modules/web.dom.iterable */ \"ac6a\");\n/* harmony import */ var core_js_modules_web_dom_iterable__WEBPACK_IMPORTED_MODULE_0___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_web_dom_iterable__WEBPACK_IMPORTED_MODULE_0__);\n/* harmony import */ var core_js_modules_es6_regexp_split__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! core-js/modules/es6.regexp.split */ \"28a5\");\n/* harmony import */ var core_js_modules_es6_regexp_split__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_regexp_split__WEBPACK_IMPORTED_MODULE_1__);\n\n\n__webpack_provided_window_dot_jQuery = jQuery;\nwindow.$ = jQuery;\n\nwindow.getCookie = function (name) {\n  var cookieValue = null;\n\n  if (document.cookie && document.cookie !== '') {\n    var cookies = document.cookie.split(';');\n\n    for (var i = 0; i < cookies.length; i++) {\n      var cookie = $.trim(cookies[i]);\n\n      if (cookie.substring(0, name.length + 1) === name + '=') {\n        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));\n        break;\n      }\n    }\n  }\n\n  return cookieValue;\n};\n\nwindow.autorModal = function () {\n  $(function () {\n    var dialog = $('#modal_autor').dialog({\n      autoOpen: false,\n      modal: true,\n      width: 500,\n      height: 340,\n      show: {\n        effect: 'blind',\n        duration: 500\n      },\n      hide: {\n        effect: 'explode',\n        duration: 500\n      }\n    });\n    $('#button-id-limpar').click(function () {\n      $('#nome_autor').text('');\n\n      function clean_if_exists(fieldname) {\n        if ($(fieldname).length > 0) {\n          $(fieldname).val('');\n        }\n      }\n\n      clean_if_exists('#id_autor');\n      clean_if_exists('#id_autoria__autor');\n    });\n    $('#button-id-pesquisar').click(function () {\n      $('#q').val('');\n      $('#div-resultado').children().remove();\n      $('#modal_autor').dialog('open');\n      $('#selecionar').attr('hidden', 'hidden');\n    });\n    $('#pesquisar').click(function () {\n      var name_in_query = $('#q').val(); // var q_0 = \"q_0=nome__icontains\"\n      // var q_1 = name_in_query\n      // query = q_1\n\n      $.get('/api/autor?q=' + name_in_query, function (data) {\n        $('#div-resultado').children().remove();\n\n        if (data.pagination.total_entries === 0) {\n          $('#selecionar').attr('hidden', 'hidden');\n          $('#div-resultado').html(\"<span class='alert'><strong>Nenhum resultado</strong></span>\");\n          return;\n        }\n\n        var select = $('<select id=\"resultados\" style=\"min-width: 90%; max-width:90%;\" size=\"5\"/>');\n        data.results.forEach(function (item) {\n          select.append($('<option>').attr('value', item.value).text(item.text));\n        });\n        $('#div-resultado').append('<br/>').append(select);\n        $('#selecionar').removeAttr('hidden', 'hidden');\n\n        if (data.pagination.total_pages > 1) {\n          $('#div-resultado').prepend('<span><br/>Mostrando 10 primeiros autores relativos a sua busca.<br/></span>');\n        }\n\n        $('#selecionar').click(function () {\n          var res = $('#resultados option:selected');\n          var id = res.val();\n          var nome = res.text();\n          $('#nome_autor').text(nome); // MateriaLegislativa pesquisa Autor via a tabela Autoria\n\n          if ($('#id_autoria__autor').length) {\n            $('#id_autoria__autor').val(id);\n          } // Protocolo pesquisa a própria tabela de Autor\n\n\n          if ($('#id_autor').length) {\n            $('#id_autor').val(id);\n          }\n\n          dialog.dialog('close');\n        });\n      });\n    });\n  });\n  /* function get_nome_autor(fieldname) {\n    if ($(fieldname).length > 0) { // se campo existir\n      if ($(fieldname).val() != \"\") { // e não for vazio\n        var id = $(fieldname).val();\n        $.get(\"/proposicao/get-nome-autor?id=\" + id, function(data, status){\n            $(\"#nome_autor\").text(data.nome);\n        });\n      }\n    }\n  }\n   get_nome_autor(\"#id_autor\");\n  get_nome_autor(\"#id_autoria__autor\"); */\n};\n\nwindow.refreshMask = function () {\n  $('.telefone').mask('(99) 9999-9999', {\n    placeholder: '(__) ____ -____'\n  });\n  $('.cpf').mask('000.000.000-00', {\n    placeholder: '___.___.___-__'\n  });\n  $('.cep').mask('00000-000', {\n    placeholder: '_____-___'\n  });\n  $('.rg').mask('0.000.000', {\n    placeholder: '_.___.___'\n  });\n  $('.titulo_eleitor').mask('0000.0000.0000.0000', {\n    placeholder: '____.____.____.____'\n  });\n  $('.dateinput').mask('00/00/0000', {\n    placeholder: '__/__/____'\n  });\n  $('.hora, input[name=hora_inicio], input[name=hora_fim], input[name=hora]').mask('00:00', {\n    placeholder: 'hh:mm'\n  });\n  $('.hora_hms').mask('00:00:00', {\n    placeholder: 'hh:mm:ss'\n  });\n  $('.timeinput').mask('00:00:00', {\n    placeholder: 'hh:mm:ss'\n  });\n  $('.cronometro').mask('00:00:00', {\n    placeholder: 'hh:mm:ss'\n  });\n};\n/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(/*! jquery */ \"1157\"), __webpack_require__(/*! jquery */ \"1157\"), __webpack_require__(/*! jquery */ \"1157\")))//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiNGUxZi5qcyIsInNvdXJjZXMiOlsid2VicGFjazovLy8uL3NyYy9nbG9iYWwvZnVuY3Rpb25zLmpzPzRlMWYiXSwic291cmNlc0NvbnRlbnQiOlsid2luZG93LmpRdWVyeSA9IGpRdWVyeVxud2luZG93LiQgPSBqUXVlcnlcblxud2luZG93LmdldENvb2tpZSA9IGZ1bmN0aW9uIChuYW1lKSB7XG4gIHZhciBjb29raWVWYWx1ZSA9IG51bGxcbiAgaWYgKGRvY3VtZW50LmNvb2tpZSAmJiBkb2N1bWVudC5jb29raWUgIT09ICcnKSB7XG4gICAgdmFyIGNvb2tpZXMgPSBkb2N1bWVudC5jb29raWUuc3BsaXQoJzsnKVxuICAgIGZvciAodmFyIGkgPSAwOyBpIDwgY29va2llcy5sZW5ndGg7IGkrKykge1xuICAgICAgdmFyIGNvb2tpZSA9ICQudHJpbShjb29raWVzW2ldKVxuICAgICAgaWYgKGNvb2tpZS5zdWJzdHJpbmcoMCwgbmFtZS5sZW5ndGggKyAxKSA9PT0gbmFtZSArICc9Jykge1xuICAgICAgICBjb29raWVWYWx1ZSA9IGRlY29kZVVSSUNvbXBvbmVudChjb29raWUuc3Vic3RyaW5nKG5hbWUubGVuZ3RoICsgMSkpXG4gICAgICAgIGJyZWFrXG4gICAgICB9XG4gICAgfVxuICB9XG4gIHJldHVybiBjb29raWVWYWx1ZVxufVxuXG53aW5kb3cuYXV0b3JNb2RhbCA9IGZ1bmN0aW9uICgpIHtcbiAgJChmdW5jdGlvbiAoKSB7XG4gICAgdmFyIGRpYWxvZyA9ICQoJyNtb2RhbF9hdXRvcicpLmRpYWxvZyh7XG4gICAgICBhdXRvT3BlbjogZmFsc2UsXG4gICAgICBtb2RhbDogdHJ1ZSxcbiAgICAgIHdpZHRoOiA1MDAsXG4gICAgICBoZWlnaHQ6IDM0MCxcbiAgICAgIHNob3c6IHtcbiAgICAgICAgZWZmZWN0OiAnYmxpbmQnLFxuICAgICAgICBkdXJhdGlvbjogNTAwXG4gICAgICB9LFxuICAgICAgaGlkZToge1xuICAgICAgICBlZmZlY3Q6ICdleHBsb2RlJyxcbiAgICAgICAgZHVyYXRpb246IDUwMFxuICAgICAgfVxuICAgIH0pXG5cbiAgICAkKCcjYnV0dG9uLWlkLWxpbXBhcicpLmNsaWNrKGZ1bmN0aW9uICgpIHtcbiAgICAgICQoJyNub21lX2F1dG9yJykudGV4dCgnJylcblxuICAgICAgZnVuY3Rpb24gY2xlYW5faWZfZXhpc3RzIChmaWVsZG5hbWUpIHtcbiAgICAgICAgaWYgKCQoZmllbGRuYW1lKS5sZW5ndGggPiAwKSB7XG4gICAgICAgICAgJChmaWVsZG5hbWUpLnZhbCgnJylcbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICBjbGVhbl9pZl9leGlzdHMoJyNpZF9hdXRvcicpXG4gICAgICBjbGVhbl9pZl9leGlzdHMoJyNpZF9hdXRvcmlhX19hdXRvcicpXG4gICAgfSlcblxuICAgICQoJyNidXR0b24taWQtcGVzcXVpc2FyJykuY2xpY2soZnVuY3Rpb24gKCkge1xuICAgICAgJCgnI3EnKS52YWwoJycpXG4gICAgICAkKCcjZGl2LXJlc3VsdGFkbycpXG4gICAgICAgIC5jaGlsZHJlbigpXG4gICAgICAgIC5yZW1vdmUoKVxuICAgICAgJCgnI21vZGFsX2F1dG9yJykuZGlhbG9nKCdvcGVuJylcbiAgICAgICQoJyNzZWxlY2lvbmFyJykuYXR0cignaGlkZGVuJywgJ2hpZGRlbicpXG4gICAgfSlcblxuICAgICQoJyNwZXNxdWlzYXInKS5jbGljayhmdW5jdGlvbiAoKSB7XG4gICAgICB2YXIgbmFtZV9pbl9xdWVyeSA9ICQoJyNxJykudmFsKClcbiAgICAgIC8vIHZhciBxXzAgPSBcInFfMD1ub21lX19pY29udGFpbnNcIlxuICAgICAgLy8gdmFyIHFfMSA9IG5hbWVfaW5fcXVlcnlcbiAgICAgIC8vIHF1ZXJ5ID0gcV8xXG5cbiAgICAgICQuZ2V0KCcvYXBpL2F1dG9yP3E9JyArIG5hbWVfaW5fcXVlcnksIGZ1bmN0aW9uIChkYXRhKSB7XG4gICAgICAgICQoJyNkaXYtcmVzdWx0YWRvJylcbiAgICAgICAgICAuY2hpbGRyZW4oKVxuICAgICAgICAgIC5yZW1vdmUoKVxuICAgICAgICBpZiAoZGF0YS5wYWdpbmF0aW9uLnRvdGFsX2VudHJpZXMgPT09IDApIHtcbiAgICAgICAgICAkKCcjc2VsZWNpb25hcicpLmF0dHIoJ2hpZGRlbicsICdoaWRkZW4nKVxuICAgICAgICAgICQoJyNkaXYtcmVzdWx0YWRvJykuaHRtbChcbiAgICAgICAgICAgIFwiPHNwYW4gY2xhc3M9J2FsZXJ0Jz48c3Ryb25nPk5lbmh1bSByZXN1bHRhZG88L3N0cm9uZz48L3NwYW4+XCJcbiAgICAgICAgICApXG4gICAgICAgICAgcmV0dXJuXG4gICAgICAgIH1cblxuICAgICAgICB2YXIgc2VsZWN0ID0gJChcbiAgICAgICAgICAnPHNlbGVjdCBpZD1cInJlc3VsdGFkb3NcIiBzdHlsZT1cIm1pbi13aWR0aDogOTAlOyBtYXgtd2lkdGg6OTAlO1wiIHNpemU9XCI1XCIvPidcbiAgICAgICAgKVxuXG4gICAgICAgIGRhdGEucmVzdWx0cy5mb3JFYWNoKGZ1bmN0aW9uIChpdGVtKSB7XG4gICAgICAgICAgc2VsZWN0LmFwcGVuZChcbiAgICAgICAgICAgICQoJzxvcHRpb24+JylcbiAgICAgICAgICAgICAgLmF0dHIoJ3ZhbHVlJywgaXRlbS52YWx1ZSlcbiAgICAgICAgICAgICAgLnRleHQoaXRlbS50ZXh0KVxuICAgICAgICAgIClcbiAgICAgICAgfSlcblxuICAgICAgICAkKCcjZGl2LXJlc3VsdGFkbycpXG4gICAgICAgICAgLmFwcGVuZCgnPGJyLz4nKVxuICAgICAgICAgIC5hcHBlbmQoc2VsZWN0KVxuICAgICAgICAkKCcjc2VsZWNpb25hcicpLnJlbW92ZUF0dHIoJ2hpZGRlbicsICdoaWRkZW4nKVxuXG4gICAgICAgIGlmIChkYXRhLnBhZ2luYXRpb24udG90YWxfcGFnZXMgPiAxKSB7XG4gICAgICAgICAgJCgnI2Rpdi1yZXN1bHRhZG8nKS5wcmVwZW5kKFxuICAgICAgICAgICAgJzxzcGFuPjxici8+TW9zdHJhbmRvIDEwIHByaW1laXJvcyBhdXRvcmVzIHJlbGF0aXZvcyBhIHN1YSBidXNjYS48YnIvPjwvc3Bhbj4nXG4gICAgICAgICAgKVxuICAgICAgICB9XG5cbiAgICAgICAgJCgnI3NlbGVjaW9uYXInKS5jbGljayhmdW5jdGlvbiAoKSB7XG4gICAgICAgICAgbGV0IHJlcyA9ICQoJyNyZXN1bHRhZG9zIG9wdGlvbjpzZWxlY3RlZCcpXG4gICAgICAgICAgbGV0IGlkID0gcmVzLnZhbCgpXG4gICAgICAgICAgbGV0IG5vbWUgPSByZXMudGV4dCgpXG5cbiAgICAgICAgICAkKCcjbm9tZV9hdXRvcicpLnRleHQobm9tZSlcblxuICAgICAgICAgIC8vIE1hdGVyaWFMZWdpc2xhdGl2YSBwZXNxdWlzYSBBdXRvciB2aWEgYSB0YWJlbGEgQXV0b3JpYVxuICAgICAgICAgIGlmICgkKCcjaWRfYXV0b3JpYV9fYXV0b3InKS5sZW5ndGgpIHtcbiAgICAgICAgICAgICQoJyNpZF9hdXRvcmlhX19hdXRvcicpLnZhbChpZClcbiAgICAgICAgICB9XG4gICAgICAgICAgLy8gUHJvdG9jb2xvIHBlc3F1aXNhIGEgcHLDs3ByaWEgdGFiZWxhIGRlIEF1dG9yXG4gICAgICAgICAgaWYgKCQoJyNpZF9hdXRvcicpLmxlbmd0aCkge1xuICAgICAgICAgICAgJCgnI2lkX2F1dG9yJykudmFsKGlkKVxuICAgICAgICAgIH1cblxuICAgICAgICAgIGRpYWxvZy5kaWFsb2coJ2Nsb3NlJylcbiAgICAgICAgfSlcbiAgICAgIH0pXG4gICAgfSlcbiAgfSlcblxuICAvKiBmdW5jdGlvbiBnZXRfbm9tZV9hdXRvcihmaWVsZG5hbWUpIHtcbiAgICBpZiAoJChmaWVsZG5hbWUpLmxlbmd0aCA+IDApIHsgLy8gc2UgY2FtcG8gZXhpc3RpclxuICAgICAgaWYgKCQoZmllbGRuYW1lKS52YWwoKSAhPSBcIlwiKSB7IC8vIGUgbsOjbyBmb3IgdmF6aW9cbiAgICAgICAgdmFyIGlkID0gJChmaWVsZG5hbWUpLnZhbCgpO1xuICAgICAgICAkLmdldChcIi9wcm9wb3NpY2FvL2dldC1ub21lLWF1dG9yP2lkPVwiICsgaWQsIGZ1bmN0aW9uKGRhdGEsIHN0YXR1cyl7XG4gICAgICAgICAgICAkKFwiI25vbWVfYXV0b3JcIikudGV4dChkYXRhLm5vbWUpO1xuICAgICAgICB9KTtcbiAgICAgIH1cbiAgICB9XG4gIH1cblxuICBnZXRfbm9tZV9hdXRvcihcIiNpZF9hdXRvclwiKTtcbiAgZ2V0X25vbWVfYXV0b3IoXCIjaWRfYXV0b3JpYV9fYXV0b3JcIik7ICovXG59XG5cbndpbmRvdy5yZWZyZXNoTWFzayA9IGZ1bmN0aW9uICgpIHtcbiAgJCgnLnRlbGVmb25lJykubWFzaygnKDk5KSA5OTk5LTk5OTknLCB7IHBsYWNlaG9sZGVyOiAnKF9fKSBfX19fIC1fX19fJyB9KVxuICAkKCcuY3BmJykubWFzaygnMDAwLjAwMC4wMDAtMDAnLCB7IHBsYWNlaG9sZGVyOiAnX19fLl9fXy5fX18tX18nIH0pXG4gICQoJy5jZXAnKS5tYXNrKCcwMDAwMC0wMDAnLCB7IHBsYWNlaG9sZGVyOiAnX19fX18tX19fJyB9KVxuICAkKCcucmcnKS5tYXNrKCcwLjAwMC4wMDAnLCB7IHBsYWNlaG9sZGVyOiAnXy5fX18uX19fJyB9KVxuICAkKCcudGl0dWxvX2VsZWl0b3InKS5tYXNrKCcwMDAwLjAwMDAuMDAwMC4wMDAwJywge1xuICAgIHBsYWNlaG9sZGVyOiAnX19fXy5fX19fLl9fX18uX19fXydcbiAgfSlcbiAgJCgnLmRhdGVpbnB1dCcpLm1hc2soJzAwLzAwLzAwMDAnLCB7IHBsYWNlaG9sZGVyOiAnX18vX18vX19fXycgfSlcbiAgJCgnLmhvcmEsIGlucHV0W25hbWU9aG9yYV9pbmljaW9dLCBpbnB1dFtuYW1lPWhvcmFfZmltXSwgaW5wdXRbbmFtZT1ob3JhXScpLm1hc2soJzAwOjAwJywge1xuICAgIHBsYWNlaG9sZGVyOiAnaGg6bW0nXG4gIH0pXG4gICQoJy5ob3JhX2htcycpLm1hc2soJzAwOjAwOjAwJywgeyBwbGFjZWhvbGRlcjogJ2hoOm1tOnNzJyB9KVxuICAkKCcudGltZWlucHV0JykubWFzaygnMDA6MDA6MDAnLCB7IHBsYWNlaG9sZGVyOiAnaGg6bW06c3MnIH0pXG4gICQoJy5jcm9ub21ldHJvJykubWFzaygnMDA6MDA6MDAnLCB7IHBsYWNlaG9sZGVyOiAnaGg6bW06c3MnIH0pXG59XG4iXSwibWFwcGluZ3MiOiI7Ozs7Ozs7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRkE7QUFJQTtBQUNBO0FBQ0E7QUFGQTtBQVRBO0FBZUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRUE7QUFDQTtBQUNBO0FBR0E7QUFDQTtBQUNBO0FBRUE7QUFDQTtBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUVBO0FBQ0E7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBSUE7QUFDQTtBQUtBO0FBRUE7QUFHQTtBQUNBO0FBQ0E7QUFDQTtBQUdBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUVBO0FBQ0E7QUFFQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRUE7Ozs7Ozs7Ozs7OztBQWFBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQUE7QUFBQTtBQUNBO0FBQ0E7QUFEQTtBQUdBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0FBQUE7QUFBQTtBQUNBO0EiLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///4e1f\n");

/***/ }),

/***/ "59ca":
/*!****************************************************************************************!*\
  !*** ./node_modules/imports-loader?window.jQuery=jquery!./src/global/jquery.runner.js ***!
  \****************************************************************************************/
/*! no exports provided */
/***/ (function(module, __webpack_exports__, __webpack_require__) {

"use strict";
eval("__webpack_require__.r(__webpack_exports__);\n/* WEBPACK VAR INJECTION */(function($) {/* harmony import */ var _home_leandro_desenvolvimento_envs_sapl_sapl_frontend_node_modules_babel_runtime_corejs2_helpers_esm_typeof__WEBPACK_IMPORTED_MODULE_0__ = __webpack_require__(/*! ./node_modules/@babel/runtime-corejs2/helpers/esm/typeof */ \"7618\");\n/* harmony import */ var core_js_modules_es6_function_name__WEBPACK_IMPORTED_MODULE_1__ = __webpack_require__(/*! core-js/modules/es6.function.name */ \"7f7f\");\n/* harmony import */ var core_js_modules_es6_function_name__WEBPACK_IMPORTED_MODULE_1___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_function_name__WEBPACK_IMPORTED_MODULE_1__);\n/* harmony import */ var core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_2__ = __webpack_require__(/*! core-js/modules/es6.array.iterator */ \"cadf\");\n/* harmony import */ var core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_2___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_array_iterator__WEBPACK_IMPORTED_MODULE_2__);\n/* harmony import */ var core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_3__ = __webpack_require__(/*! core-js/modules/es6.promise */ \"551c\");\n/* harmony import */ var core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_3___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es6_promise__WEBPACK_IMPORTED_MODULE_3__);\n/* harmony import */ var core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_4__ = __webpack_require__(/*! core-js/modules/es7.promise.finally */ \"097d\");\n/* harmony import */ var core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_4___default = /*#__PURE__*/__webpack_require__.n(core_js_modules_es7_promise_finally__WEBPACK_IMPORTED_MODULE_4__);\n/*** IMPORTS FROM imports-loader ***/\nvar window = (window || {});\nwindow.jQuery = __webpack_require__(/*! jquery */ \"1157\");\n\n\n\n\n\n\n\n/* eslint-disable */\n\n/*!\n * jQuery-runner - v2.3.3 - 2014-08-06\n * https://github.com/jylauril/jquery-runner/\n * Copyright (c) 2014 Jyrki Laurila <https://github.com/jylauril>\n */\n(function () {\n  var Runner, formatTime, meta, pad, runners, uid, _$, _requestAnimationFrame, _uid;\n\n  meta = {\n    version: \"2.3.3\",\n    name: \"jQuery-runner\"\n  };\n  _$ = $;\n\n  if (!(_$ && _$.fn)) {\n    throw new Error('[' + meta.name + '] jQuery or jQuery-like library is required for this plugin to work');\n  }\n\n  runners = {};\n\n  pad = function pad(num) {\n    return (num < 10 ? '0' : '') + num;\n  };\n\n  _uid = 1;\n\n  uid = function uid() {\n    return 'runner' + _uid++;\n  };\n\n  _requestAnimationFrame = function (win, raf) {\n    return win['r' + raf] || win['webkitR' + raf] || win['mozR' + raf] || win['msR' + raf] || function (fn) {\n      return setTimeout(fn, 30);\n    };\n  }(this, 'equestAnimationFrame');\n\n  formatTime = function formatTime(time, settings) {\n    var i, len, ms, output, prefix, separator, step, steps, value, _i, _len;\n\n    settings = settings || {};\n    steps = [3600000, 60000, 1000, 10];\n    separator = ['', ':', ':', '.'];\n    prefix = '';\n    output = '';\n    ms = settings.milliseconds;\n    len = steps.length;\n    value = 0;\n\n    if (time < 0) {\n      time = Math.abs(time);\n      prefix = '-';\n    }\n\n    for (i = _i = 0, _len = steps.length; _i < _len; i = ++_i) {\n      step = steps[i];\n      value = 0;\n\n      if (time >= step) {\n        value = Math.floor(time / step);\n        time -= value * step;\n      }\n\n      if ((value || i > 1 || output) && (i !== len - 1 || ms)) {\n        output += (output ? separator[i] : '') + pad(value);\n      }\n    }\n\n    return prefix + output;\n  };\n\n  Runner = function () {\n    function Runner(items, options, start) {\n      var id;\n\n      if (!(this instanceof Runner)) {\n        return new Runner(items, options, start);\n      }\n\n      this.items = items;\n      id = this.id = uid();\n      this.settings = _$.extend({}, this.settings, options);\n      runners[id] = this;\n      items.each(function (index, element) {\n        _$(element).data('runner', id);\n      });\n      this.value(this.settings.startAt);\n\n      if (start || this.settings.autostart) {\n        this.start();\n      }\n    }\n\n    Runner.prototype.running = false;\n    Runner.prototype.updating = false;\n    Runner.prototype.finished = false;\n    Runner.prototype.interval = null;\n    Runner.prototype.total = 0;\n    Runner.prototype.lastTime = 0;\n    Runner.prototype.startTime = 0;\n    Runner.prototype.lastLap = 0;\n    Runner.prototype.lapTime = 0;\n    Runner.prototype.settings = {\n      autostart: false,\n      countdown: false,\n      stopAt: null,\n      startAt: 0,\n      milliseconds: true,\n      format: null\n    };\n\n    Runner.prototype.value = function (value) {\n      this.items.each(function (_this) {\n        return function (item, element) {\n          var action;\n          item = _$(element);\n          action = item.is('input') ? 'val' : 'text';\n          item[action](_this.format(value));\n        };\n      }(this));\n    };\n\n    Runner.prototype.format = function (value) {\n      var format;\n      format = this.settings.format;\n      format = _$.isFunction(format) ? format : formatTime;\n      return format(value, this.settings);\n    };\n\n    Runner.prototype.update = function () {\n      var countdown, delta, settings, stopAt, time;\n\n      if (!this.updating) {\n        this.updating = true;\n        settings = this.settings;\n        time = _$.now();\n        stopAt = settings.stopAt;\n        countdown = settings.countdown;\n        delta = time - this.lastTime;\n        this.lastTime = time;\n\n        if (countdown) {\n          this.total -= delta;\n        } else {\n          this.total += delta;\n        }\n\n        if (stopAt !== null && (countdown && this.total <= stopAt || !countdown && this.total >= stopAt)) {\n          this.total = stopAt;\n          this.finished = true;\n          this.stop();\n          this.fire('runnerFinish');\n        }\n\n        this.value(this.total);\n        this.updating = false;\n      }\n    };\n\n    Runner.prototype.fire = function (event) {\n      this.items.trigger(event, this.info());\n    };\n\n    Runner.prototype.start = function () {\n      var step;\n\n      if (!this.running) {\n        this.running = true;\n\n        if (!this.startTime || this.finished) {\n          this.reset();\n        }\n\n        this.lastTime = _$.now();\n\n        step = function (_this) {\n          return function () {\n            if (_this.running) {\n              _this.update();\n\n              _requestAnimationFrame(step);\n            }\n          };\n        }(this);\n\n        _requestAnimationFrame(step);\n\n        this.fire('runnerStart');\n      }\n    };\n\n    Runner.prototype.stop = function () {\n      if (this.running) {\n        this.running = false;\n        this.update();\n        this.fire('runnerStop');\n      }\n    };\n\n    Runner.prototype.toggle = function () {\n      if (this.running) {\n        this.stop();\n      } else {\n        this.start();\n      }\n    };\n\n    Runner.prototype.lap = function () {\n      var lap, last;\n      last = this.lastTime;\n      lap = last - this.lapTime;\n\n      if (this.settings.countdown) {\n        lap = -lap;\n      }\n\n      if (this.running || lap) {\n        this.lastLap = lap;\n        this.lapTime = last;\n      }\n\n      last = this.format(this.lastLap);\n      this.fire('runnerLap');\n      return last;\n    };\n\n    Runner.prototype.reset = function (stop) {\n      var nowTime;\n\n      if (stop) {\n        this.stop();\n      }\n\n      nowTime = _$.now();\n\n      if (typeof this.settings.startAt === 'number' && !this.settings.countdown) {\n        nowTime -= this.settings.startAt;\n      }\n\n      this.startTime = this.lapTime = this.lastTime = nowTime;\n      this.total = this.settings.startAt;\n      this.value(this.total);\n      this.finished = false;\n      this.fire('runnerReset');\n    };\n\n    Runner.prototype.info = function () {\n      var lap;\n      lap = this.lastLap || 0;\n      return {\n        running: this.running,\n        finished: this.finished,\n        time: this.total,\n        formattedTime: this.format(this.total),\n        startTime: this.startTime,\n        lapTime: lap,\n        formattedLapTime: this.format(lap),\n        settings: this.settings\n      };\n    };\n\n    return Runner;\n  }();\n\n  _$.fn.runner = function (method, options, start) {\n    var id, runner;\n\n    if (!method) {\n      method = 'init';\n    }\n\n    if (Object(_home_leandro_desenvolvimento_envs_sapl_sapl_frontend_node_modules_babel_runtime_corejs2_helpers_esm_typeof__WEBPACK_IMPORTED_MODULE_0__[\"default\"])(method) === 'object') {\n      start = options;\n      options = method;\n      method = 'init';\n    }\n\n    id = this.data('runner');\n    runner = id ? runners[id] : false;\n\n    switch (method) {\n      case 'init':\n        new Runner(this, options, start);\n        break;\n\n      case 'info':\n        if (runner) {\n          return runner.info();\n        }\n\n        break;\n\n      case 'reset':\n        if (runner) {\n          runner.reset(options);\n        }\n\n        break;\n\n      case 'lap':\n        if (runner) {\n          return runner.lap();\n        }\n\n        break;\n\n      case 'start':\n      case 'stop':\n      case 'toggle':\n        if (runner) {\n          return runner[method]();\n        }\n\n        break;\n\n      case 'version':\n        return meta.version;\n\n      default:\n        _$.error('[' + meta.name + '] Method ' + method + ' does not exist');\n\n    }\n\n    return this;\n  };\n\n  _$.fn.runner.format = formatTime;\n}).call(window);\n\n/* WEBPACK VAR INJECTION */}.call(this, __webpack_require__(/*! jquery */ \"1157\")))//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiNTljYS5qcyIsInNvdXJjZXMiOlsid2VicGFjazovLy8uL3NyYy9nbG9iYWwvanF1ZXJ5LnJ1bm5lci5qcz9mNmNmIl0sInNvdXJjZXNDb250ZW50IjpbIi8qIGVzbGludC1kaXNhYmxlICovXG4vKiFcbiAqIGpRdWVyeS1ydW5uZXIgLSB2Mi4zLjMgLSAyMDE0LTA4LTA2XG4gKiBodHRwczovL2dpdGh1Yi5jb20vanlsYXVyaWwvanF1ZXJ5LXJ1bm5lci9cbiAqIENvcHlyaWdodCAoYykgMjAxNCBKeXJraSBMYXVyaWxhIDxodHRwczovL2dpdGh1Yi5jb20vanlsYXVyaWw+XG4gKi9cbihmdW5jdGlvbigpIHtcbiAgdmFyIFJ1bm5lciwgZm9ybWF0VGltZSwgbWV0YSwgcGFkLCBydW5uZXJzLCB1aWQsIF8kLCBfcmVxdWVzdEFuaW1hdGlvbkZyYW1lLCBfdWlkXG5cbiAgbWV0YSA9IHtcbiAgICB2ZXJzaW9uOiBcIjIuMy4zXCIsXG4gICAgbmFtZTogXCJqUXVlcnktcnVubmVyXCJcbiAgfVxuXG4gIF8kID0gJFxuXG4gIGlmICghKF8kICYmIF8kLmZuKSkge1xuICAgIHRocm93IG5ldyBFcnJvcignWycgKyBtZXRhLm5hbWUgKyAnXSBqUXVlcnkgb3IgalF1ZXJ5LWxpa2UgbGlicmFyeSBpcyByZXF1aXJlZCBmb3IgdGhpcyBwbHVnaW4gdG8gd29yaycpXG4gIH1cblxuICBydW5uZXJzID0ge31cblxuICBwYWQgPSBmdW5jdGlvbihudW0pIHtcbiAgICByZXR1cm4gKG51bSA8IDEwID8gJzAnIDogJycpICsgbnVtXG4gIH1cblxuICBfdWlkID0gMVxuXG4gIHVpZCA9IGZ1bmN0aW9uKCkge1xuICAgIHJldHVybiAncnVubmVyJyArIF91aWQrK1xuICB9XG5cbiAgX3JlcXVlc3RBbmltYXRpb25GcmFtZSA9IChmdW5jdGlvbih3aW4sIHJhZikge1xuICAgIHJldHVybiB3aW5bJ3InICsgcmFmXSB8fCB3aW5bJ3dlYmtpdFInICsgcmFmXSB8fCB3aW5bJ21velInICsgcmFmXSB8fCB3aW5bJ21zUicgKyByYWZdIHx8IGZ1bmN0aW9uKGZuKSB7XG4gICAgICByZXR1cm4gc2V0VGltZW91dChmbiwgMzApXG4gICAgfVxuICB9KSh0aGlzLCAnZXF1ZXN0QW5pbWF0aW9uRnJhbWUnKVxuXG4gIGZvcm1hdFRpbWUgPSBmdW5jdGlvbih0aW1lLCBzZXR0aW5ncykge1xuICAgIHZhciBpLCBsZW4sIG1zLCBvdXRwdXQsIHByZWZpeCwgc2VwYXJhdG9yLCBzdGVwLCBzdGVwcywgdmFsdWUsIF9pLCBfbGVuXG4gICAgc2V0dGluZ3MgPSBzZXR0aW5ncyB8fCB7fVxuICAgIHN0ZXBzID0gWzM2MDAwMDAsIDYwMDAwLCAxMDAwLCAxMF1cbiAgICBzZXBhcmF0b3IgPSBbJycsICc6JywgJzonLCAnLiddXG4gICAgcHJlZml4ID0gJydcbiAgICBvdXRwdXQgPSAnJ1xuICAgIG1zID0gc2V0dGluZ3MubWlsbGlzZWNvbmRzXG4gICAgbGVuID0gc3RlcHMubGVuZ3RoXG4gICAgdmFsdWUgPSAwXG4gICAgaWYgKHRpbWUgPCAwKSB7XG4gICAgICB0aW1lID0gTWF0aC5hYnModGltZSlcbiAgICAgIHByZWZpeCA9ICctJ1xuICAgIH1cbiAgICBmb3IgKGkgPSBfaSA9IDAsIF9sZW4gPSBzdGVwcy5sZW5ndGg7IF9pIDwgX2xlbjsgaSA9ICsrX2kpIHtcbiAgICAgIHN0ZXAgPSBzdGVwc1tpXVxuICAgICAgdmFsdWUgPSAwXG4gICAgICBpZiAodGltZSA+PSBzdGVwKSB7XG4gICAgICAgIHZhbHVlID0gTWF0aC5mbG9vcih0aW1lIC8gc3RlcClcbiAgICAgICAgdGltZSAtPSB2YWx1ZSAqIHN0ZXBcbiAgICAgIH1cbiAgICAgIGlmICgodmFsdWUgfHwgaSA+IDEgfHwgb3V0cHV0KSAmJiAoaSAhPT0gbGVuIC0gMSB8fCBtcykpIHtcbiAgICAgICAgb3V0cHV0ICs9IChvdXRwdXQgPyBzZXBhcmF0b3JbaV0gOiAnJykgKyBwYWQodmFsdWUpXG4gICAgICB9XG4gICAgfVxuICAgIHJldHVybiBwcmVmaXggKyBvdXRwdXRcbiAgfVxuXG4gIFJ1bm5lciA9IChmdW5jdGlvbigpIHtcbiAgICBmdW5jdGlvbiBSdW5uZXIoaXRlbXMsIG9wdGlvbnMsIHN0YXJ0KSB7XG4gICAgICB2YXIgaWRcbiAgICAgIGlmICghKHRoaXMgaW5zdGFuY2VvZiBSdW5uZXIpKSB7XG4gICAgICAgIHJldHVybiBuZXcgUnVubmVyKGl0ZW1zLCBvcHRpb25zLCBzdGFydClcbiAgICAgIH1cbiAgICAgIHRoaXMuaXRlbXMgPSBpdGVtc1xuICAgICAgaWQgPSB0aGlzLmlkID0gdWlkKClcbiAgICAgIHRoaXMuc2V0dGluZ3MgPSBfJC5leHRlbmQoe30sIHRoaXMuc2V0dGluZ3MsIG9wdGlvbnMpXG4gICAgICBydW5uZXJzW2lkXSA9IHRoaXNcbiAgICAgIGl0ZW1zLmVhY2goZnVuY3Rpb24oaW5kZXgsIGVsZW1lbnQpIHtcbiAgICAgICAgXyQoZWxlbWVudCkuZGF0YSgncnVubmVyJywgaWQpXG4gICAgICB9KVxuICAgICAgdGhpcy52YWx1ZSh0aGlzLnNldHRpbmdzLnN0YXJ0QXQpXG4gICAgICBpZiAoc3RhcnQgfHwgdGhpcy5zZXR0aW5ncy5hdXRvc3RhcnQpIHtcbiAgICAgICAgdGhpcy5zdGFydCgpXG4gICAgICB9XG4gICAgfVxuXG4gICAgUnVubmVyLnByb3RvdHlwZS5ydW5uaW5nID0gZmFsc2VcblxuICAgIFJ1bm5lci5wcm90b3R5cGUudXBkYXRpbmcgPSBmYWxzZVxuXG4gICAgUnVubmVyLnByb3RvdHlwZS5maW5pc2hlZCA9IGZhbHNlXG5cbiAgICBSdW5uZXIucHJvdG90eXBlLmludGVydmFsID0gbnVsbFxuXG4gICAgUnVubmVyLnByb3RvdHlwZS50b3RhbCA9IDBcblxuICAgIFJ1bm5lci5wcm90b3R5cGUubGFzdFRpbWUgPSAwXG5cbiAgICBSdW5uZXIucHJvdG90eXBlLnN0YXJ0VGltZSA9IDBcblxuICAgIFJ1bm5lci5wcm90b3R5cGUubGFzdExhcCA9IDBcblxuICAgIFJ1bm5lci5wcm90b3R5cGUubGFwVGltZSA9IDBcblxuICAgIFJ1bm5lci5wcm90b3R5cGUuc2V0dGluZ3MgPSB7XG4gICAgICBhdXRvc3RhcnQ6IGZhbHNlLFxuICAgICAgY291bnRkb3duOiBmYWxzZSxcbiAgICAgIHN0b3BBdDogbnVsbCxcbiAgICAgIHN0YXJ0QXQ6IDAsXG4gICAgICBtaWxsaXNlY29uZHM6IHRydWUsXG4gICAgICBmb3JtYXQ6IG51bGxcbiAgICB9XG5cbiAgICBSdW5uZXIucHJvdG90eXBlLnZhbHVlID0gZnVuY3Rpb24odmFsdWUpIHtcbiAgICAgIHRoaXMuaXRlbXMuZWFjaCgoZnVuY3Rpb24oX3RoaXMpIHtcbiAgICAgICAgcmV0dXJuIGZ1bmN0aW9uKGl0ZW0sIGVsZW1lbnQpIHtcbiAgICAgICAgICB2YXIgYWN0aW9uXG4gICAgICAgICAgaXRlbSA9IF8kKGVsZW1lbnQpXG4gICAgICAgICAgYWN0aW9uID0gaXRlbS5pcygnaW5wdXQnKSA/ICd2YWwnIDogJ3RleHQnXG4gICAgICAgICAgaXRlbVthY3Rpb25dKF90aGlzLmZvcm1hdCh2YWx1ZSkpXG4gICAgICAgIH1cbiAgICAgIH0pKHRoaXMpKVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUuZm9ybWF0ID0gZnVuY3Rpb24odmFsdWUpIHtcbiAgICAgIHZhciBmb3JtYXRcbiAgICAgIGZvcm1hdCA9IHRoaXMuc2V0dGluZ3MuZm9ybWF0XG4gICAgICBmb3JtYXQgPSBfJC5pc0Z1bmN0aW9uKGZvcm1hdCkgPyBmb3JtYXQgOiBmb3JtYXRUaW1lXG4gICAgICByZXR1cm4gZm9ybWF0KHZhbHVlLCB0aGlzLnNldHRpbmdzKVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUudXBkYXRlID0gZnVuY3Rpb24oKSB7XG4gICAgICB2YXIgY291bnRkb3duLCBkZWx0YSwgc2V0dGluZ3MsIHN0b3BBdCwgdGltZVxuICAgICAgaWYgKCF0aGlzLnVwZGF0aW5nKSB7XG4gICAgICAgIHRoaXMudXBkYXRpbmcgPSB0cnVlXG4gICAgICAgIHNldHRpbmdzID0gdGhpcy5zZXR0aW5nc1xuICAgICAgICB0aW1lID0gXyQubm93KClcbiAgICAgICAgc3RvcEF0ID0gc2V0dGluZ3Muc3RvcEF0XG4gICAgICAgIGNvdW50ZG93biA9IHNldHRpbmdzLmNvdW50ZG93blxuICAgICAgICBkZWx0YSA9IHRpbWUgLSB0aGlzLmxhc3RUaW1lXG4gICAgICAgIHRoaXMubGFzdFRpbWUgPSB0aW1lXG4gICAgICAgIGlmIChjb3VudGRvd24pIHtcbiAgICAgICAgICB0aGlzLnRvdGFsIC09IGRlbHRhXG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgdGhpcy50b3RhbCArPSBkZWx0YVxuICAgICAgICB9XG4gICAgICAgIGlmIChzdG9wQXQgIT09IG51bGwgJiYgKChjb3VudGRvd24gJiYgdGhpcy50b3RhbCA8PSBzdG9wQXQpIHx8ICghY291bnRkb3duICYmIHRoaXMudG90YWwgPj0gc3RvcEF0KSkpIHtcbiAgICAgICAgICB0aGlzLnRvdGFsID0gc3RvcEF0XG4gICAgICAgICAgdGhpcy5maW5pc2hlZCA9IHRydWVcbiAgICAgICAgICB0aGlzLnN0b3AoKVxuICAgICAgICAgIHRoaXMuZmlyZSgncnVubmVyRmluaXNoJylcbiAgICAgICAgfVxuICAgICAgICB0aGlzLnZhbHVlKHRoaXMudG90YWwpXG4gICAgICAgIHRoaXMudXBkYXRpbmcgPSBmYWxzZVxuICAgICAgfVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUuZmlyZSA9IGZ1bmN0aW9uKGV2ZW50KSB7XG4gICAgICB0aGlzLml0ZW1zLnRyaWdnZXIoZXZlbnQsIHRoaXMuaW5mbygpKVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUuc3RhcnQgPSBmdW5jdGlvbigpIHtcbiAgICAgIHZhciBzdGVwXG4gICAgICBpZiAoIXRoaXMucnVubmluZykge1xuICAgICAgICB0aGlzLnJ1bm5pbmcgPSB0cnVlXG4gICAgICAgIGlmICghdGhpcy5zdGFydFRpbWUgfHwgdGhpcy5maW5pc2hlZCkge1xuICAgICAgICAgIHRoaXMucmVzZXQoKVxuICAgICAgICB9XG4gICAgICAgIHRoaXMubGFzdFRpbWUgPSBfJC5ub3coKVxuICAgICAgICBzdGVwID0gKGZ1bmN0aW9uKF90aGlzKSB7XG4gICAgICAgICAgcmV0dXJuIGZ1bmN0aW9uKCkge1xuICAgICAgICAgICAgaWYgKF90aGlzLnJ1bm5pbmcpIHtcbiAgICAgICAgICAgICAgX3RoaXMudXBkYXRlKClcbiAgICAgICAgICAgICAgX3JlcXVlc3RBbmltYXRpb25GcmFtZShzdGVwKVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH1cbiAgICAgICAgfSkodGhpcylcbiAgICAgICAgX3JlcXVlc3RBbmltYXRpb25GcmFtZShzdGVwKVxuICAgICAgICB0aGlzLmZpcmUoJ3J1bm5lclN0YXJ0JylcbiAgICAgIH1cbiAgICB9XG5cbiAgICBSdW5uZXIucHJvdG90eXBlLnN0b3AgPSBmdW5jdGlvbigpIHtcbiAgICAgIGlmICh0aGlzLnJ1bm5pbmcpIHtcbiAgICAgICAgdGhpcy5ydW5uaW5nID0gZmFsc2VcbiAgICAgICAgdGhpcy51cGRhdGUoKVxuICAgICAgICB0aGlzLmZpcmUoJ3J1bm5lclN0b3AnKVxuICAgICAgfVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUudG9nZ2xlID0gZnVuY3Rpb24oKSB7XG4gICAgICBpZiAodGhpcy5ydW5uaW5nKSB7XG4gICAgICAgIHRoaXMuc3RvcCgpXG4gICAgICB9IGVsc2Uge1xuICAgICAgICB0aGlzLnN0YXJ0KClcbiAgICAgIH1cbiAgICB9XG5cbiAgICBSdW5uZXIucHJvdG90eXBlLmxhcCA9IGZ1bmN0aW9uKCkge1xuICAgICAgdmFyIGxhcCwgbGFzdFxuICAgICAgbGFzdCA9IHRoaXMubGFzdFRpbWVcbiAgICAgIGxhcCA9IGxhc3QgLSB0aGlzLmxhcFRpbWVcbiAgICAgIGlmICh0aGlzLnNldHRpbmdzLmNvdW50ZG93bikge1xuICAgICAgICBsYXAgPSAtbGFwXG4gICAgICB9XG4gICAgICBpZiAodGhpcy5ydW5uaW5nIHx8IGxhcCkge1xuICAgICAgICB0aGlzLmxhc3RMYXAgPSBsYXBcbiAgICAgICAgdGhpcy5sYXBUaW1lID0gbGFzdFxuICAgICAgfVxuICAgICAgbGFzdCA9IHRoaXMuZm9ybWF0KHRoaXMubGFzdExhcClcbiAgICAgIHRoaXMuZmlyZSgncnVubmVyTGFwJylcbiAgICAgIHJldHVybiBsYXN0XG4gICAgfVxuXG4gICAgUnVubmVyLnByb3RvdHlwZS5yZXNldCA9IGZ1bmN0aW9uKHN0b3ApIHtcbiAgICAgIHZhciBub3dUaW1lXG4gICAgICBpZiAoc3RvcCkge1xuICAgICAgICB0aGlzLnN0b3AoKVxuICAgICAgfVxuICAgICAgbm93VGltZSA9IF8kLm5vdygpXG4gICAgICBpZiAodHlwZW9mIHRoaXMuc2V0dGluZ3Muc3RhcnRBdCA9PT0gJ251bWJlcicgJiYgIXRoaXMuc2V0dGluZ3MuY291bnRkb3duKSB7XG4gICAgICAgIG5vd1RpbWUgLT0gdGhpcy5zZXR0aW5ncy5zdGFydEF0XG4gICAgICB9XG4gICAgICB0aGlzLnN0YXJ0VGltZSA9IHRoaXMubGFwVGltZSA9IHRoaXMubGFzdFRpbWUgPSBub3dUaW1lXG4gICAgICB0aGlzLnRvdGFsID0gdGhpcy5zZXR0aW5ncy5zdGFydEF0XG4gICAgICB0aGlzLnZhbHVlKHRoaXMudG90YWwpXG4gICAgICB0aGlzLmZpbmlzaGVkID0gZmFsc2VcbiAgICAgIHRoaXMuZmlyZSgncnVubmVyUmVzZXQnKVxuICAgIH1cblxuICAgIFJ1bm5lci5wcm90b3R5cGUuaW5mbyA9IGZ1bmN0aW9uKCkge1xuICAgICAgdmFyIGxhcFxuICAgICAgbGFwID0gdGhpcy5sYXN0TGFwIHx8IDBcbiAgICAgIHJldHVybiB7XG4gICAgICAgIHJ1bm5pbmc6IHRoaXMucnVubmluZyxcbiAgICAgICAgZmluaXNoZWQ6IHRoaXMuZmluaXNoZWQsXG4gICAgICAgIHRpbWU6IHRoaXMudG90YWwsXG4gICAgICAgIGZvcm1hdHRlZFRpbWU6IHRoaXMuZm9ybWF0KHRoaXMudG90YWwpLFxuICAgICAgICBzdGFydFRpbWU6IHRoaXMuc3RhcnRUaW1lLFxuICAgICAgICBsYXBUaW1lOiBsYXAsXG4gICAgICAgIGZvcm1hdHRlZExhcFRpbWU6IHRoaXMuZm9ybWF0KGxhcCksXG4gICAgICAgIHNldHRpbmdzOiB0aGlzLnNldHRpbmdzXG4gICAgICB9XG4gICAgfVxuXG4gICAgcmV0dXJuIFJ1bm5lclxuXG4gIH0pKClcblxuICBfJC5mbi5ydW5uZXIgPSBmdW5jdGlvbihtZXRob2QsIG9wdGlvbnMsIHN0YXJ0KSB7XG4gICAgdmFyIGlkLCBydW5uZXJcbiAgICBpZiAoIW1ldGhvZCkge1xuICAgICAgbWV0aG9kID0gJ2luaXQnXG4gICAgfVxuICAgIGlmICh0eXBlb2YgbWV0aG9kID09PSAnb2JqZWN0Jykge1xuICAgICAgc3RhcnQgPSBvcHRpb25zXG4gICAgICBvcHRpb25zID0gbWV0aG9kXG4gICAgICBtZXRob2QgPSAnaW5pdCdcbiAgICB9XG4gICAgaWQgPSB0aGlzLmRhdGEoJ3J1bm5lcicpXG4gICAgcnVubmVyID0gaWQgPyBydW5uZXJzW2lkXSA6IGZhbHNlXG4gICAgc3dpdGNoIChtZXRob2QpIHtcbiAgICAgIGNhc2UgJ2luaXQnOlxuICAgICAgICBuZXcgUnVubmVyKHRoaXMsIG9wdGlvbnMsIHN0YXJ0KVxuICAgICAgICBicmVha1xuICAgICAgY2FzZSAnaW5mbyc6XG4gICAgICAgIGlmIChydW5uZXIpIHtcbiAgICAgICAgICByZXR1cm4gcnVubmVyLmluZm8oKVxuICAgICAgICB9XG4gICAgICAgIGJyZWFrXG4gICAgICBjYXNlICdyZXNldCc6XG4gICAgICAgIGlmIChydW5uZXIpIHtcbiAgICAgICAgICBydW5uZXIucmVzZXQob3B0aW9ucylcbiAgICAgICAgfVxuICAgICAgICBicmVha1xuICAgICAgY2FzZSAnbGFwJzpcbiAgICAgICAgaWYgKHJ1bm5lcikge1xuICAgICAgICAgIHJldHVybiBydW5uZXIubGFwKClcbiAgICAgICAgfVxuICAgICAgICBicmVha1xuICAgICAgY2FzZSAnc3RhcnQnOlxuICAgICAgY2FzZSAnc3RvcCc6XG4gICAgICBjYXNlICd0b2dnbGUnOlxuICAgICAgICBpZiAocnVubmVyKSB7XG4gICAgICAgICAgcmV0dXJuIHJ1bm5lclttZXRob2RdKClcbiAgICAgICAgfVxuICAgICAgICBicmVha1xuICAgICAgY2FzZSAndmVyc2lvbic6XG4gICAgICAgIHJldHVybiBtZXRhLnZlcnNpb25cbiAgICAgIGRlZmF1bHQ6XG4gICAgICAgIF8kLmVycm9yKCdbJyArIG1ldGEubmFtZSArICddIE1ldGhvZCAnICsgbWV0aG9kICsgJyBkb2VzIG5vdCBleGlzdCcpXG4gICAgfVxuICAgIHJldHVybiB0aGlzXG4gIH1cblxuICBfJC5mbi5ydW5uZXIuZm9ybWF0ID0gZm9ybWF0VGltZVxufSkuY2FsbCh3aW5kb3cpXG4iXSwibWFwcGluZ3MiOiI7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7O0FBQUE7QUFDQTtBQUFBOzs7OztBQUtBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUZBO0FBS0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBRUE7QUFFQTtBQUVBO0FBRUE7QUFFQTtBQUVBO0FBRUE7QUFFQTtBQUVBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBTkE7QUFDQTtBQVFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQVJBO0FBVUE7QUFDQTtBQUNBO0FBRUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFBQTtBQUNBO0FBQUE7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFBQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQUE7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQUFBO0FBQ0E7QUFDQTtBQTlCQTtBQUNBO0FBOEJBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0EiLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///59ca\n");

/***/ })

/******/ });