/*!
 * Copyright (c) 2016 Wikimedia Foundation and contributors.
 * Licensed under the GPL v3+ license
 */
$( () => {
	'use strict';

	// eslint-disable-next-line no-jquery/no-global-selector
	$( '[data-toggle="tooltip"]' ).tooltip();

	/* eslint-disable camelcase */
	window.notify_badge_id = 'live_notify_badge';
	window.notify_refresh_period = 60000;
	window.notify_api_url = '/alerts/api/unread_count/';
	/* eslint-enable camelcase */
	// eslint-disable-next-line no-undef
	register_notifier( fill_notification_badge );

	// Work around for
	// https://github.com/yourlabs/django-autocomplete-light/issues/772
	// eslint-disable-next-line
	const $csrf = $( 'form :input[name="csrfmiddlewaretoken"]' );
	if ( $csrf.length > 0 ) {
		document.csrftoken = $csrf[ 0 ].value;
	}
} );
