import tinymce from 'tinymce'

import 'tinymce/themes/silver'
import 'tinymce/icons/default'
import 'tinymce/models/dom/index'
import 'tinymce/skins/ui/oxide/skin.min.css'

import 'tinymce/plugins/code'
import 'tinymce/plugins/advlist'
import 'tinymce/plugins/link'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/table'

import './langs/pt_BR.js'

window.tinymce = tinymce
// Títulos (h1-h6) vindos de estilos de título do Word ou de páginas web
// chegam em negrito e não podem ser desfeitos pelo botão de negrito nem
// por "remover formatação". Converte-os em parágrafos, mantendo o alinhamento.
function colarTitulosComoParagrafo (editor, args) {
  args.node.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(function (titulo) {
    const paragrafo = document.createElement('p')
    if (titulo.style.textAlign) {
      paragrafo.style.textAlign = titulo.style.textAlign
    }
    while (titulo.firstChild) {
      paragrafo.appendChild(titulo.firstChild)
    }
    titulo.replaceWith(paragrafo)
  })
}

window.initTextRichEditor = function (elements, readonly = false, paste_as_text = false, paste_titulos_como_paragrafo = false) {
  const configTinymce = {
    selector: elements === null || elements === undefined ? 'textarea' : elements,
    language: 'pt_BR',
    branding: false,
    forced_root_block: 'p',
    paste_as_text,
    plugins: 'table lists advlist link code',
    toolbar: 'undo redo | blocks | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link | code | removeformat ',
    menubar: 'file edit view insert format table',
    license_key: 'gpl'
  }
  if (paste_titulos_como_paragrafo) {
    configTinymce.paste_postprocess = colarTitulosComoParagrafo
  }
  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }
  return window.tinymce.init(configTinymce)
}
