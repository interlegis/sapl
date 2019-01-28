import 'bootstrap'

import 'webpack-jquery-ui/dialog'
import 'webpack-jquery-ui/sortable'

import './functions'

import(
  /* webpackChunkName: "jquery_mask_plugin" */
  'jquery-mask-plugin')
  .then(jquery_mask_plugin => {
    jquery_mask_plugin.default()
  })

import(
  /* webpackChunkName: "image_cropping" */
  './image_cropping')
  .then(image_cropping => {
    image_cropping.default()
  })

// eslint-disable-next-line
require('imports-loader?window.jQuery=jquery!./jquery.runner.js')

window.autorModal()
window.refreshMask()

// "sapl-oficial-theme": "../../sapl-oficial-theme",
