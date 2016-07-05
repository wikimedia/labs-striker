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
MEMBER_DN=${2:=$ADMIN_DN}

# Crappy random id generator
NEW_GID=$(echo -n "${TOOL}" | sha1sum | awk '{print $1}' | tr '[:lower:]' '[:upper:]')
NEW_GID=$(echo "ibase=16; ${NEW_GID:(-3)}" | bc)
NEW_GID=$(( $NEW_GID + 1001 ))

/usr/bin/ldapadd -x -D "${ADMIN_DN}" -w "${ADMIN_PASS}" <<LDIF
dn: cn=tools.${TOOL},${TOOL_BASE_DN}
changetype: add
objectClass: groupOfNames
objectClass: posixGroup
objectClass: top
cn: tools.${TOOL}
gidNumber: ${NEW_GID}
member: ${MEMBER_DN}
LDIF
