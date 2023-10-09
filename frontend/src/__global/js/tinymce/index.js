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
window.initTextRichEditor = function (elements, readonly = false, paste_as_text = false) {
  const configTinymce = {
    selector: elements === null || elements === undefined ? 'textarea' : elements,
    language: 'pt_BR',
    branding: false,
    forced_root_block: 'p',
    toolbar: "...| removeformat | ...",
    paste_as_text,
    plugins: 'table lists advlist link code',
    toolbar: 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link | code',
    menubar: 'file edit view insert format table'
  }
  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }
  window.tinymce.init(configTinymce)
}
