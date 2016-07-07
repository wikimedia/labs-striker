#!/usr/bin/env bash
# Hack a tool into the testing LDAP server setup with MediaWiki-Vagrant's
# role::striker.
#
# Usage: add-tool.sh NAME [DN_OF_MAINTAINER]

TOOL=${1:?TOOL required}
BASE_DN="dc=wmftest,dc=net"
TOOL_BASE_DN="ou=servicegroups,${BASE_DN}"
ADMIN_DN="cn=admin,${BASE_DN}"
ADMIN_PASS="vagrant_admin"

/usr/bin/ldapadd -x -D "${ADMIN_DN}" -w "${ADMIN_PASS}" <<LDIF
dn: cn=tools.${TOOL},${TOOL_BASE_DN}
changetype: delete
LDIF
