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
            logger.debug("Creating default instance")
            cls._default_instance = cls(
                settings.WIKITECH_URL,
                consumer_token=settings.WIKITECH_CONSUMER_TOKEN,
                consumer_secret=settings.WIKITECH_CONSUMER_SECRET,
                access_token=settings.WIKITECH_ACCESS_TOKEN,
                access_secret=settings.WIKITECH_ACCESS_SECRET,
            )
        return cls._default_instance

    def __init__(
        self,
        url,
        consumer_token=None,
        consumer_secret=None,
        access_token=None,
        access_secret=None,
    ):
        self.url = url
        self.site = self._site_for_url(
            url, consumer_token, consumer_secret, access_token, access_secret
        )

    @classmethod
    def _site_for_url(
        cls,
        url,
        consumer_token=None,
        consumer_secret=None,
        access_token=None,
        access_secret=None,
    ):
        parts = urllib.parse.urlparse(url)
        host = parts.netloc
        if parts.scheme != "https":
            host = (parts.scheme, parts.netloc)
        force_login = consumer_token is not None
        return mwclient.Site(
            host,
            consumer_token=consumer_token,
            consumer_secret=consumer_secret,
            access_token=access_token,
            access_secret=access_secret,
            clients_useragent="Striker",
            force_login=force_login,
        )

    def query_blocks_ip(self, ip):
        result = self.site.api("query", formatversion=2, list="blocks", bkip=ip)
        return result["query"]["blocks"]

    def get_page(self, title, follow_redirects=True):
        """Get a Page object."""
        page = self.site.Pages[title]
        while follow_redirects and page.redirect:
            page = next(page.links())
        return page

    def user_talk_page(self, username):
        """Get a user's talk page."""
        return self.get_page("User_talk:{}".format(username))
