/*!
 * Copyright (c) 2016 Wikimedia Foundation and contributors.
 * Licensed under the GPL v3+ license
 */
$(function () {
    "use strict";
    $('[data-toggle="tooltip"]').tooltip();

    notify_badge_id='live_notify_badge';
    notify_refresh_period=60000;
    notify_api_url='/alerts/api/unread_count/';
    register_notifier(fill_notification_badge);
})
