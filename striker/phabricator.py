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

from django.conf import settings
import json
import logging
import requests


logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, message, code, result):
        self.message = message
        self.code = code
        self.result = result

    def __str__(self):
        return '%s (%s)' % (self.message, self.code)


class Client(object):
    """Phabricator client"""
    _default_instance = None

    @classmethod
    def default_client(cls):
        """Get a Phabricator client using the default credentials."""
        if cls._default_instance is None:
            logger.debug('Creating default instance')
            cls._default_instance = cls(
                settings.PHABRICATOR_URL,
                settings.PHABRICATOR_USER,
                settings.PHABRICATOR_TOKEN)
        return cls._default_instance

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
        logger.debug('%s result: %s', path, resp)
        if resp['error_code'] is not None:
            raise APIError(
                resp['error_info'],
                resp['error_code'],
                resp.get('result', None))
        return resp['result']

    def user_ldapquery(self, names):
        """Lookup Phabricator user data associated with LDAP sn values."""
        try:
            r = self.post('user.ldapquery', {
                'ldapnames': names,
                'offset': 0,
                'limit': len(names),
            })
        except APIError, e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown or missing ldap names' in e.message:
                logger.warn(e.message)
                if e.result is None:
                    raise KeyError('Users not found for %s' % ', '.join(names))
                else:
                    # Return the partial result
                    r = e.result
            else:
                raise e
        else:
            return r

    def user_mediawikiquery(self, names):
        """Lookup Phabricator user data associated with mediawiki accounts."""
        try:
            r = self.post('user.mediawikiquery', {
                'names': names,
                'offset': 0,
                'limit': len(names),
            })
        except APIError, e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown or missing mediawiki names' in e.message:
                logger.warn(e.message)
                if e.result is None:
                    raise KeyError('Users not found for %s' % ', '.join(names))
                else:
                    # Return the partial result
                    r = e.result
            else:
                raise e
        else:
            return r

    def get_repository(self, name):
        """Lookup information on a diffusion repository by name."""
        r = self.post('diffusion.repository.search', {
            'constraints': {
                'name': name,
            },
            'attachments': {
                'uris': True,
            },
            'limit': 1,
        })
        if 'data' in r and len(r['data']) == 1:
            return r['data'][0]
        else:
            raise KeyError('Repository %s not found' % name)

    def create_repository(self, name, owners):
        """Create a new diffusion repository."""
        # Create policy allowing the phids given in owners plus repo-admins
        custom_policy = self.create_repo_policy(owners)

        r = self.post('diffusion.repository.edit', {
            'transactions': [
                {'type': 'vcs', 'value': 'git'},
                {'type': 'name', 'value': name},
                {'type': 'shortName', 'value': name},
                {'type': 'allowDangerousChanges', 'value': True},
                {'type': 'status', 'value': 'active'},
                {'type': 'publish', 'value': True},
                {'type': 'autoclose', 'value': False},
                {'type': 'policy.push', 'value': custom_policy},
                {'type': 'view', 'value': 'public'},
                {'type': 'edit', 'value': custom_policy},
            ],
        })
        return r['object']

    def create_repo_policy(self, owners):
        """Create an edit policy for a diffusion repository."""
        r = self.post('policy.create', {
            'objectType': 'REPO',
            'default': 'deny',
            'policy': [
                {
                    'action': 'allow',
                    'rule': 'PhabricatorProjectsPolicyRule',
                    'value': [settings.PHABRICATOR_REPO_ADMIN_GROUP],
                },
                {
                    'action': 'allow',
                    'rule': 'PhabricatorUsersPolicyRule',
                    'value': owners,
                }
            ],
        })
        return r['phid']

    def get_policies(self, phids):
        """Get security policy information."""
        try:
            r = self.post('policy.query', {
                'phids': phids,
                'offset': 0,
                'limit': len(phids),
            })
        except APIError, e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown policies' in e.message:
                logger.warn(e.message)
                if e.result is None:
                    raise KeyError(
                        'Policies not found for %s' % ', '.join(phids))
                else:
                    # Return the partial result
                    r = e.result
            else:
                raise e
        else:
            return r

    def get_phids(self, phids):
        """Get phid information."""
        return self.post('phid.query', {
            'phids': phids,
        })

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
