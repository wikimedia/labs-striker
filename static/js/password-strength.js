/*!
 * Copyright (c) 2016 Wikimedia Foundation and contributors.
 * Licensed under the GPL v3+ license
 */
$(function () {
    "use strict";
    var $passwd = $('.check-password-strength-input'),
        $meter = $('#password-strength-meter'),
        $cells = $meter.children('.password-strength-cell'),
        personal = [],
        allStyles = 'zxcvbn-0 zxcvbn-1 zxcvbn-2 zxcvbn-3 zxcvbn-4';

    $('.personal').each(function () {
        $(this).val().split("@").forEach(function (val) {
            personal.push(val);
        });
    });

    $passwd.on('input', function (e) {
        var score = zxcvbn($passwd.val(), personal).score,
            idx = 1;
        $cells.removeClass(allStyles);
        $cells.children('span').addClass('hide');
        $cells.each(function () {
            if (idx > score) { return false; }
            var $this = $(this);
            $this.addClass('zxcvbn-' + score);
            if (idx == score) {
                $this.children('span').removeClass('hide');
            }
            idx++;
        });
    });
});
