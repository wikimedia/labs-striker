#!/usr/bin/env bash
# Hack a maintainer into the testing LDAP server setup with
# MediaWiki-Vagrant's role::striker.
#
# Usage: add-maintainer.sh TOOL DN_OF_MAINTAINER

TOOL=${1:?TOOL required}
MEMBER_DN=${2:?DN required}
BASE_DN="dc=wmftest,dc=net"
TOOL_BASE_DN="ou=servicegroups,${BASE_DN}"
ADMIN_DN="cn=admin,${BASE_DN}"
ADMIN_PASS="vagrant_admin"

/usr/bin/ldapmodify -x -D "${ADMIN_DN}" -w "${ADMIN_PASS}" <<LDIF
dn: cn=tools.${TOOL},${TOOL_BASE_DN}
changetype: modify
add: member
member: ${MEMBER_DN}
LDIF
