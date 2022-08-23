# -*- coding: utf-8 -*-
#
# Copyright (c) 2022 Wikimedia Foundation and contributors.
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

import requests

from django.conf import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, message, code, result):
        self.message = message
        self.code = code
        self.result = result

    def __str__(self):
        return "{0} ({1})".format(self.message, self.code)


class Client(object):
    """GitLab client."""

    _default_instance = None

    @classmethod
    def default_client(cls):
        """Get a GitLab client using the default credentials."""
        if cls._default_instance is None:
            logger.debug("Creating default instance")
            cls._default_instance = cls(
                settings.GITLAB_URL,
                settings.GITLAB_ACCESS_TOKEN,
                settings.GITLAB_REPO_NAMESPACE_NAME,
                settings.GITLAB_REPO_NAMESPACE_ID,
            )
        return cls._default_instance

    def __init__(self, url, token, repo_namespace_name, repo_namespace_id):
        """Initialize instance."""
        self.url = url
        self.token = token
        self.repo_namespace_name = repo_namespace_name
        self.repo_namespace_id = repo_namespace_id
        self.session = requests.Session()
        self.headers = {
            "PRIVATE-TOKEN": self.token,
            "Content-Type": "application/json",
        }

    def http_request(self, verb, path, payload=None, params=None):
        r = self.session.request(
            method=verb,
            url="{0}/api/v4/{1}".format(self.url, path),
            headers=self.headers,
            params=params,
            json=payload,
        )
        if 200 <= r.status_code < 300:
            return r.json()

        err_msg = r.content
        err_json = r.json()
        if "message" in err_json:
            err_msg = err_json["message"]
        if "error" in err_json:
            err_msg = err_json["error"]
        raise APIError(err_msg, r.status_code, r)

    def post(self, path, payload=None):
        resp = self.http_request("POST", path, payload=payload)
        logger.debug("POST %s: %s", path, resp)
        return resp

    def get(self, path, params=None):
        resp = self.http_request("GET", path, params=params)
        logger.debug("GET %s: %s", path, resp)
        return resp

    def user_lookup(self, uids):
        """Lookup GitHub user data for a list of LDAP uid values."""
        uids = list(filter(None, uids))
        r = []
        for uid in uids:
            try:
                r.extend(self.get(
                    "users",
                    {
                        "provider": settings.GITLAB_PROVIDER,
                        "extern_uid": settings.GITLAB_EXTERN_FORMAT.format(
                            uid
                        ),
                    }
                ))
            except APIError:
                logger.exception("Failed to lookup user '%s'", uid)
        return r

    def get_repository_by_id(self, repo_id):
        """Get data about a git repository."""
        return self.get("projects/{}/".format(repo_id))

    def get_repository_by_name(self, name):
        """Get data about a git repository."""
        try:
            return self.get(
                "projects/{}%2F{}/".format(
                    urllib.parse.quote(self.repo_namespace_name),
                    urllib.parse.quote(name),
                )
            )
        except APIError as e:
            if e.code == 404:
                raise KeyError('Repository {0} not found'.format(name))
            raise e

    def create_repository(self, name, owners):
        """Create a new git repository."""
        repo = self.post("projects/", {
            "name": name,
            "namespace_id": self.repo_namespace_id,
            "visibility": "public",
        })
        owners = self.user_lookup(owners)
        self.post("projects/{}/members".format(repo["id"]), {
            "user_id": ",".join(str(o["id"]) for o in owners),
            "access_level": 50,  # Owner
        })
        return self.get_repository_by_id(repo["id"])
