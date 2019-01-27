import 'bootstrap'
import 'jquery-mask-plugin'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'

import './functions'

import './image_cropping'

// eslint-disable-next-line
require('imports-loader?window.jQuery=jquery!./jquery.runner.js')

window.autorModal()
window.refreshMask()

// "sapl-oficial-theme": "../../sapl-oficial-theme",
