
require("imports-loader?window.jQuery=jquery!./jquery.runner.js");

import "jquery-mask-plugin";

import "webpack-jquery-ui/dialog";
import "webpack-jquery-ui/sortable";

import "bootstrap";

import "./functions";

import "./image_cropping";

window.jQuery = jQuery
window.$ = jQuery

window.autorModal();
window.refreshMask();
