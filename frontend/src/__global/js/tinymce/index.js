
import tinymce from 'tinymce/tinymce'
import './langs/pt_BR.js'

import 'tinymce/themes/silver'
import 'tinymce/icons/default'

import 'tinymce/plugins/table'
import 'tinymce/plugins/lists'
import 'tinymce/plugins/code'
import 'tinymce/plugins/visualblocks'

import 'tinymce/skins/ui/oxide/skin.css'

window.tinymce = tinymce

window.removeTinymce = function () {
  while (window.tinymce.editors.length > 0) {
    window.tinymce.remove(window.tinymce.editors[0])
  }
}

window.initTextRichEditor = function (elements, readonly = false) {
  window.removeTinymce()
  const configTinymce = {
    selector: elements === null || elements === undefined ? 'textarea' : elements,
    forced_root_block: '',
    min_height: 200,
    language: 'pt_BR',
    branding: false,
    content_css: 'default',
    plugins: ['lists table code visualblocks'],
    menubar: 'edit view format table tools',
    toolbar: 'undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent'
  }
  if (readonly) {
    configTinymce.readonly = 1
    configTinymce.menubar = false
    configTinymce.toolbar = false
  }
  window.tinymce.init(configTinymce)
}
