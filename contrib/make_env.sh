#!/usr/bin/env bash
# Generate a .env file for local development
mkpass() {
    head /dev/urandom | LC_ALL=C tr -dc A-Za-z0-9 | head -c ${1:-20}
}
set -euo pipefail
cat > ${1:?Missing target file} << _EOF
# Local development settings
# See docker-compose.yaml for available envvars.

# Local user on the host system (for example your laptop)
LOCAL_UID=$(id -u)
LOCAL_GID=$(id -g)

DJANGO_SECRET_KEY=$(mkpass 48)
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=*

LOGGING_HANDLERS=console
LOGGING_LEVEL=DEBUG

DB_ENGINE=striker.db
DB_NAME=striker
DB_USER=striker
DB_PASSWORD=striker
DB_HOST=mariadb.local.wmftest.net
DB_PORT=3306

LDAP_SERVER_URI=ldap://openldap.local.wmftest.net:389
LDAP_BIND_USER=cn=writer,dc=wmftest,dc=net
LDAP_BIND_PASSWORD=docker_writer
LDAP_USER_SEARCH_BASE=ou=People,dc=wmftest,dc=net
LDAP_BASE_DN=dc=wmftest,dc=net
AUTH_LDAP_PASSWORD_RESET_URL=http://ldapwiki.local.wmftest.net:8083/wiki/Special:PasswordReset
STAFF_GROUP_DN=cn=tools.admin,ou=servicegroups,dc=wmftest,dc=net
SUPERUSER_GROUP_DN=cn=tools.admin,ou=servicegroups,dc=wmftest,dc=net
TOOLS_MAINTAINER_BASE_DN=ou=people,dc=wmftest,dc=net
TOOLS_TOOL_BASE_DN=ou=servicegroups,dc=wmftest,dc=net
TOOLS_DISABLED_POLICY_ENTRY=cn=disabled,ou=ppolicies,dc=wmftest,dc=net

CACHE_BACKEND=django.core.cache.backends.locmem.LocMemCache
CACHE_LOCATION=default-cache

SSL_CANONICAL_HOST=striker.local.wmftest.net

OAUTH_MWURL=http://sulwiki.local.wmftest.net:8082/w/index.php

PHABRICATOR_URL=http://phabricator.local.wmftest.net:8081

WIKITECH_URL=http://ldapwiki.local.wmftest.net:8083

OPENSTACK_URL=http://keystone.local.wmftest.net:5000/v3
OPENSTACK_USER=admin
OPENSTACK_PASSWORD=admin

GITLAB_URL=http://gitlab.local.wmftest.net:8084
GITLAB_PROVIDER=ldapmain
GITLAB_EXTERN_FORMAT="uid={0.uid},ou=people,dc=wmftest,dc=net"

SITE_ENVIRONMENT_BANNER="LOCAL DEVELOPMENT ENVIRONMENT"

#####################################################################
## Values to set manually when following initial setup instructions

GITLAB_ACCESS_TOKEN=
GITLAB_REPO_NAMESPACE_ID=

OAUTH_CONSUMER_KEY=
OAUTH_CONSUMER_SECRET=

PHABRICATOR_TOKEN=
PHABRICATOR_REPO_ADMIN_GROUP=
PHABRICATOR_PARENT_PROJECT=

WIKITECH_CONSUMER_TOKEN=
WIKITECH_CONSUMER_SECRET=
WIKITECH_ACCESS_TOKEN=
WIKITECH_ACCESS_SECRET=
_EOF
