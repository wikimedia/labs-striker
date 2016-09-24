/*!
 * Copyright (c) 2016 Wikimedia Foundation and contributors.
 * Licensed under the GPL v3+ license
 */
$(function () {
    "use strict";
    // Integrate parsley output with our bootstrap forms and css.
    // Inspired by tutorial by Jimmy Bonney
    // <http://jimmybonney.com/articles/parsley_js_twitter_bootstrap/>
    window.Parsley.on('field:error', function(el) {
        "use strict";
        var $el = el.$element;
        if ($el.is('input[type=text]')) {
            $el.next('.form-control-feedback').remove();
            $el.after(
                    '<span class="glyphicon glyphicon-ban-circle form-control-feedback" aria-hidden="true"></span>');
        }
    });
    window.Parsley.on('field:success', function(el) {
        "use strict";
        var $el = el.$element;
        if ($el.is('input[type=text]')) {
            $el.next('.form-control-feedback').remove();
            $el.after(
                    '<span class="glyphicon glyphicon-ok-circle form-control-feedback" aria-hidden="true"></span>');
        }
    });
    $('form.parsley').parsley({
        successClass: 'has-success has-feedback',
        errorClass: 'has-error has-feedback',
        classHandler: function(el) {
            return el.$element.closest('.form-group');
        },
        errorsContainer: function(el) {
            return el.$element.closest('.form-group');
        },
        errorsWrapper: '<span class="help-block"></span>',
        errorTemplate: '<span></span>'
    });
    // Fire the focusin event so that parsley will validate the initial value
    $(document.activeElement).focus();
})
