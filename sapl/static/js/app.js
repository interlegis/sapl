
function initTinymce(elements, readonly=false) {
    removeTinymce();
    var config_tinymce = {
        force_br_newlines : false,
        force_p_newlines : false,
        forced_root_block : '',
        plugins: ["table save code"],
        menubar: "edit format table tools",
        toolbar: "undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent",
        tools: "inserttable",
    }

    if (readonly) {
      config_tinymce.readonly = 1;
      config_tinymce.menubar = false;
      config_tinymce.toolbar = false;
    }

    if (elements != null) {
        config_tinymce['elements'] = elements;
        config_tinymce['mode'] = "exact";
        }
    else
        config_tinymce['mode'] = "textareas";

    tinymce.init(config_tinymce);
}

function removeTinymce() {
    while (tinymce.editors.length > 0) {
        tinymce.remove(tinymce.editors[0]);
    }
}

function refreshDatePicker() {
    $.datepicker.setDefaults($.datepicker.regional['pt-BR']);
    $('.dateinput').datepicker();
}

function refreshMask() {
    $('.telefone').mask("(99) 9999-9999", {placeholder:"(__) ____ -____"});
    $('.cpf').mask("000.000.000-00", {placeholder:"___.___.___-__"});
    $('.cep').mask("00000-000", {placeholder:"_____-___"});
    $('.rg').mask("0.000.000", {placeholder:"_.___.___"});
    $('.titulo_eleitor').mask("0000.0000.0000.0000", {placeholder:"____.____.____.____"});
    $('.dateinput').mask('00/00/0000', {placeholder:"__/__/____"});
    $('.hora').mask("00:00", {placeholder:"hh:mm"});
    $('.hora_hms').mask("00:00:00", {placeholder:"hh:mm:ss"});
    $('.timeinput').mask("00:00:00", {placeholder:"hh:mm:ss"});
    $('.cronometro').mask("00:00:00", {placeholder:"hh:mm:ss"});
}

function OptionalCustomFrontEnd() {
    // Adaptações opcionais de layout com a presença de JS.
    // Não implementar customizações que a funcionalidade que fique dependente.
    var instance;
    if (!(this instanceof OptionalCustomFrontEnd)) {
        if (!instance) {
            instance = new OptionalCustomFrontEnd();
        }
        return instance;
    }
    instance = this;
    OptionalCustomFrontEnd = function() {
        return instance;
    }
    instance.customCheckBoxAndRadio = function() {
        $('[type=radio], [type=checkbox]').each(function() {
            var _this = $(this)
            var _controls = _this.closest('.controls');
            _controls && _controls.find(':file').length == 0 && !_controls.hasClass('controls-radio-checkbox') && _controls.addClass('controls-radio-checkbox');
            _controls.find(':file').length > 0 && _controls.addClass('controls-file');
        });
    }
    instance.customCheckBoxAndRadioWithoutLabel = function() {

        $('[type=radio], [type=checkbox]').each(function() {
            let _this = $(this)
            
            if (this.id === undefined || this.id.length === 0) {
                return 
            }
                        
            let _label = _this.closest('label')

            if (_label.length === 0) {
                _label = $('label[for='+this.id+']');
                if (_label.length === 0) {
                    _label = $('<label for='+this.id+'/>').insertBefore(this)
                }
            }

            if (this.type === "checkbox") {
                _label.prepend(_this);

                var _div = _label.closest('.checkbox');
                if (_div.length == 0) {
                    _label.addClass('checkbox-inline')
                }

                _this.checkbox();
            }
            else if (this.type === "radio") {
                _label.prepend(_this);

                var _div = _label.closest('.radio');
                if (_div.length == 0) {
                    _label.addClass('radio-inline')
                }

                _this.radio();

            }

        });
    }
    instance.init = function() {
        this.customCheckBoxAndRadio();
        this.customCheckBoxAndRadioWithoutLabel();
    }
    instance.init();
}

$(document).ready(function(){
    refreshDatePicker();
    refreshMask();
    initTinymce("texto-rico");

    //OptionalCustomFrontEnd();
});

