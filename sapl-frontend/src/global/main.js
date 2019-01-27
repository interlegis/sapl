// eslint-disable-next-line
import 'jquery-mask-plugin'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'

import './functions'
import 'bootstrap'

import './image_cropping'

require('imports-loader?window.jQuery=jquery!./jquery.runner.js')
// require(THEME_CUSTOM + '/src/assets/img/authenticated.png')

window.autorModal()
window.refreshMask()

