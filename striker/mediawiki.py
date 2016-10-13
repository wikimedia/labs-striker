# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Striker.
#
# Striker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Striker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Striker.  If not, see <http://www.gnu.org/licenses/>.

import logging
import urllib.parse

import mwclient

from django.conf import settings


logger = logging.getLogger(__name__)


class Client(object):
    """MediaWiki client"""
    _default_instance = None

    @classmethod
    def default_client(cls):
        """Get a MediaWiki client using the default credentials."""
        if cls._default_instance is None:
            logger.debug('Creating default instance')
            cls._default_instance = cls(settings.WIKITECH_URL)
        return cls._default_instance

    def __init__(self, url):
        self.url = url
        self.site = self._site_for_url(url)
        self.site.force_login = False

    @classmethod
    def _site_for_url(cls, url):
        parts = urllib.parse.urlparse(url)
        host = parts.netloc
        if parts.scheme != 'https':
            host = (parts.scheme, parts.netloc)
        return mwclient.Site(host, clients_useragent='Striker')

    def query_users_cancreate(self, *users):
        """Check to see if the given usernames could be created or not.

        Note: if this Client is authenticated to the target wiki, the result
        that you get from this request may or may not be the same result that
        an anonymous user would get.
        """
        result = self.site.api(
            'query', formatversion=2,
            list='users',
            usprop='cancreate', ususers='|'.join(users),
        )

        logger.debug(result)
        # Example result:
        # {'query': {'users': [{'missing': True, 'name': 'Puppet',
        # 'cancreate': False, 'cancreateerror': [{'message':
        # 'titleblacklist-forbidden-new-account', 'params': ['
        # ^(User:)?puppet$ <newaccountonly>', 'Puppet'], 'type': 'error'}]}],
        # 'userinfo': {'anon': True, 'messages': False, 'name':
        # '137.164.12.107', 'id': 0}}, 'batchcomplete': True}
        # TODO: error handling
        return result['query']['users']

    def get_message(self, message, *params, lang='en'):
        result = self.site.api(
            'query', formatversion=2,
            meta='allmessages',
            ammessages=message, amargs='|'.join(params), amlang=lang,
        )
        # TODO: error handling
        return result['query']['allmessages'][0]['content']
