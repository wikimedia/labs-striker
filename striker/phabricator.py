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
import logging
import requests

from django.conf import settings


logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, message, code, result):
        self.message = message
        self.code = code
        self.result = result

    def __str__(self):
        return '{0} ({1})'.format(self.message, self.code)


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
        r = requests.post('{0}/api/{1}'.format(self.url, path), data={
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
        """Lookup Phabricator user data associated with LDAP cn values."""
        names = list(filter(None, names))
        try:
            r = self.post('user.ldapquery', {
                'ldapnames': names,
                'offset': 0,
                'limit': len(names),
            })
        except APIError as e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown or missing ldap names' in e.message:
                logger.warning(e.message)
                if e.result is None:
                    raise KeyError(
                        'Users not found for {0}'.format(', '.join(names)))
                else:
                    # Return the partial result
                    r = e.result
            else:
                raise e
        else:
            return r

    def user_mediawikiquery(self, names):
        """Lookup Phabricator user data associated with mediawiki accounts."""
        names = list(filter(None, names))
        try:
            r = self.post('user.mediawikiquery', {
                'names': names,
                'offset': 0,
                'limit': len(names),
            })
        except APIError as e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown or missing mediawiki names' in e.message:
                logger.warning(e.message)
                if e.result is None:
                    raise KeyError(
                        'Users not found for {0}'.format(', '.join(names)))
                else:
                    # Return the partial result
                    r = e.result
            else:
                raise e
        else:
            return r

    def user_external_lookup(self, ldap=None, mw=None):
        """Lookup Phabricator user data associated with external accounts."""
        r = []
        if ldap is not None and len(ldap) and ldap[0] is not None:
            try:
                r.extend(self.user_ldapquery(ldap))
            except KeyError as e:
                logger.debug(e)
                pass
        if mw is not None and len(mw) and mw[0] is not None:
            try:
                mw_r = self.user_mediawikiquery(mw)
            except KeyError as e:
                logger.debug(e)
                pass
            else:
                # Deep merge results
                for u in mw_r:
                    logger.debug(u)
                    for u2 in r:
                        if u2['phid'] == u['phid']:
                            # Decorate existing record with found mw username
                            u2[u'mediawiki_username'] = u['mediawiki_username']
                            logger.debug('Added to %s', u2['phid'])
                            break
                    else:
                        # An else attached to a for loop is reached if a break
                        # was not issued inside the for loop.
                        logger.debug('Fall through for %s', u['phid'])
                        r.append(u)
        return r

    def get_repository(self, name):
        """Lookup information on a diffusion repository by name."""
        r = self.post('diffusion.repository.search', {
            'constraints': {
                'shortNames': [name],
            },
            'attachments': {
                'uris': True,
            },
            'order': 'name',
        })
        if 'data' in r:
            for repo in r['data']:
                if repo['fields']['name'] == name:
                    return repo
        raise KeyError('Repository {0} not found'.format(name))

    def get_repository_by_phid(self, phid):
        """Lookup information on a diffusion repository by phid."""
        r = self.post('diffusion.repository.search', {
            'constraints': {
                'phids': [phid],
            },
            'attachments': {
                'uris': True,
            },
        })
        if 'data' in r and len(r['data']) == 1:
            return r['data'][0]
        raise KeyError('Repository {0} not found'.format(phid))

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
                {'type': 'publish', 'value': False},  # T227508
                {'type': 'policy.push', 'value': custom_policy},
                {'type': 'view', 'value': 'public'},
                {'type': 'edit', 'value': custom_policy},
            ],
        })
        obj = r['object']
        repo = self.get_repository_by_phid(obj['phid'])
        self._repository_hide_http_url(repo)
        return repo

    def repository_admin_only(self, repo_phid):
        """Set repository to be admin controlled only."""
        # Empty owners list makes an admin only policy
        admin_policy = self.create_repo_policy([])

        self.post('diffusion.repository.edit', {
            'objectIdentifier': repo_phid,
            'transactions': [
                {'type': 'policy.push', 'value': admin_policy},
                {'type': 'edit', 'value': admin_policy},
            ],
        })
        return self.get_repository_by_phid(repo_phid)

    def repository_mirror(self, repo_phid, upstream_uri):
        """Make a repo a mirror of an upstream."""
        repo = self.get_repository_by_phid(repo_phid)
        for uri in repo['attachments']['uris']['uris']:
            if uri['fields']['io']['default'] == 'readwrite':
                self.post('diffusion.uri.edit', {
                    'objectIdentifier': uri['phid'],
                    'transactions': [
                        {'type': 'io', 'value': 'read'},
                    ],
                })
        self.post('diffusion.uri.edit', {
            'transactions': [
                {'type': 'repository', 'value': repo_phid},
                {'type': 'uri', 'value': upstream_uri},
                {'type': 'io', 'value': 'observe'},
                {'type': 'display', 'value': 'never'},
            ],
        })
        self.post('diffusion.repository.edit', {
            'objectIdentifier': repo_phid,
            'transactions': [
                {
                    'type': 'description',
                    'value': 'Diffusion mirror of {}'.format(upstream_uri),
                },
                {
                    'type': 'defaultBranch',
                    'value': 'main',
                },
            ],
        })
        return self.get_repository_by_phid(repo_phid)

    def repository_is_mirror(self, repo_phid):
        """Is the given repo a mirror of some upstream?"""
        repo = self.get_repository_by_phid(repo_phid)
        for uri in repo['attachments']['uris']['uris']:
            if uri['fields']['io']['raw'] == 'observe':
                return True
        return False

    def _repository_hide_http_url(self, repo):
        """Hide http URI if we also have an https URI."""
        https = self._repository_get_uri_with_scheme(repo, 'https://id')
        http = self._repository_get_uri_with_scheme(repo, 'http://id')
        if https is not None and http is not None:
            try:
                self.post('diffusion.uri.edit', {
                    'transactions': [
                        {'type': 'display', 'value': 'never'},
                    ],
                    'objectIdentifier': http['phid'],
                })
                return True
            except APIError:
                logger.exception(
                    'Failed to hide http uri for repo %s', repo['phid'])
                return False
        return False

    def _repository_get_uri_with_scheme(self, repo, scheme):
        for uri in repo['attachments']['uris']['uris']:
            if uri['fields']['uri']['raw'] == scheme:
                return uri
        return None

    def create_repo_policy(self, owners):
        """Create an edit policy for a diffusion repository."""
        policy = [
            {
                'action': 'allow',
                'rule': 'PhabricatorProjectsPolicyRule',
                'value': [settings.PHABRICATOR_REPO_ADMIN_GROUP],
            },
        ]
        if owners:
            policy.append(
                {
                    'action': 'allow',
                    'rule': 'PhabricatorUsersPolicyRule',
                    'value': owners,
                }
            )
        r = self.post('policy.create', {
            'objectType': 'REPO',
            'default': 'deny',
            'policy': policy,
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
        except APIError as e:
            if e.code == 'ERR-INVALID-PARAMETER' and \
                    'Unknown policies' in e.message:
                logger.warning(e.message)
                if e.result is None:
                    raise KeyError(
                        'Policies not found for {0}'.format(', '.join(phids)))
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
        raise KeyError('Task {0} not found'.format(task))

    def comment(self, task, comment):
        """Add a comment to a task.
        :param task: Task number (e.g. T12345)
        :param comment: Comment to add to task
        """
        self.post('maniphest.edit', {
            'objectIdentifier': self.task(task)['phid'],
            'transactions': [
                {'type': 'comment', 'value': comment},
            ],
        })

    def get_project(self, name):
        """Lookup information on a project by name."""
        r = self.post('project.search', {
            'constraints': {
                'query': 'title:{}'.format(json.dumps(name))
            },
            'attachments': {
                'uris': True,
            },
            'order': 'name',
        })
        if 'data' in r:
            for repo in r['data']:
                if repo['fields']['name'] == name:
                    return repo
        raise KeyError('Repository {0} not found'.format(name))

    def get_project_by_phid(self, phid):
        """Lookup information on a project by phid."""
        r = self.post('project.search', {
            'constraints': {
                'phids': [phid],
            },
            'attachments': {
                'uris': True,
            },
        })
        if 'data' in r and len(r['data']) == 1:
            return r['data'][0]
        raise KeyError('Project {0} not found'.format(phid))

    def create_project(self, name, *, members, parent, description):
        """Creates a project with the given name"""
        r = self.post('project.edit', {
            'transactions': [
                {'type': 'name', 'value': name},
                {'type': 'parent', 'value': parent},
                {'type': 'description', 'value': description},
                {'type': 'members.add', 'value': members},
            ],
        })
        obj = r['object']
        repo = self.get_project_by_phid(obj['phid'])
        return repo
