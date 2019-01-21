import jQuery from "jquery";

import "bootstrap";

import "jquery-mask-plugin";

import "webpack-jquery-ui/dialog";
import "webpack-jquery-ui/sortable";

import "./functions";
require('imports-loader?window.jQuery=jquery!./jquery.runner.js');
window.$ = window.jQuery = jQuery;

window.autorModal();
window.refreshMask();
