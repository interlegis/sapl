import 'bootstrap'
import 'jquery-mask-plugin'

import 'jquery-ui/dist/jquery-ui'
import 'jquery-ui/ui/widgets/dialog'
import 'jquery-ui/ui/widgets/sortable'
import 'jquery-ui/ui/widgets/datepicker'
import 'jquery-ui/ui/widgets/autocomplete'
import 'jquery-ui/ui/i18n/datepicker-pt-BR'

import * as moment from 'moment'
import 'moment/locale/pt-br'

import './js/tinymce'
import './js/image_cropping'
import './js/functions'
import './js/jquery.runner'

import '@fortawesome/fontawesome-free/css/all.css'
import 'jquery-ui-themes/themes/cupertino/jquery-ui.min.css'
import './scss/app.scss'

window.$ = $
window.jQuery = $

window.moment = moment

window.autorModal()
window.refreshMask()
window.refreshDatePicker()

window.initTextRichEditor('#texto-rico')
