import jQuery from "jquery";
window.$ = window.jQuery = jQuery;

require('imports-loader?window.jQuery=jquery!./jquery.runner.js');

import "jquery-mask-plugin";

import "webpack-jquery-ui/dialog";
import "webpack-jquery-ui/sortable";

import "./functions";


window.autorModal();
window.refreshMask();
