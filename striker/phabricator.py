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

import json
import requests


class APIError(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code

    def __str__(self):
        return '%s (%s)' % (self.message, self.code)


class Client(object):
    """Phabricator client"""
    def __init__(self, url, username, token):
        self.url = url
        self.username = username
        self.session = {
            'token': token,
        }

    def post(self, path, data):
        data['__conduit__'] = self.session
        r = requests.post('%s/api/%s' % (self.url, path), data={
            'params': json.dumps(data),
            'output': 'json',
        })
        resp = r.json()
        if resp['error_code'] is not None:
            raise APIError(resp['error_info'], resp['error_code'])
        return resp['result']

    def user_by_ldap(self, name):
        try:
            r = self.post('user.ldapquery', {
                'ldapnames': [name],
                'offset': 0,
                'limit': 1,
            })[0]
        except APIError, e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown or missing ldap names' in e.message:
                raise KeyError('User not found for %s' % name)
            else:
                raise e
        else:
            if r['ldap_username'] != name:
                raise KeyError('User not found for %s' % name)
            return r

    def task(self, task):
        r = self.post('phid.lookup', {'names': [task]})
        if task in r:
            return r[task]
        raise KeyError('Task %s not found' % task)

    def comment(self, task, comment):
        """Add a comment to a task.
        :param task: Task number (e.g. T12345)
        :param comment: Comment to add to task
        """
        phid = self.task(task)['phid']
        self.post('maniphest.update', {
            'phid': phid,
            'comments': comment,
        })
