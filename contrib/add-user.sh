#!/usr/bin/env bash
# Hack a user into the testing LDAP server setup with MediaWiki-Vagrant's
# role::striker. This is a quick fix to work around differences between
# accounts created with OSM (prod) and LdapAuth (mw-vagrant).
#
# Usage: add-user.sh SHELL_USER_NAME [WIKI_USER_NAME]

NEW_UID=${1:?SHELL_USER_NAME required}
NEW_CN=${2:-$NEW_UID}
BASE_DN="dc=wmftest,dc=net"
USER_BASE_DN="ou=People,${BASE_DN}"
ADMIN_DN="cn=admin,${BASE_DN}"
ADMIN_PASS="vagrant_admin"

# Crappy random id generator
USER_ID=$(echo -n "${NEW_UID}" | sha1sum | awk '{print $1}' | tr '[:lower:]' '[:upper:]')
USER_ID=$(echo "ibase=16; ${USER_ID:(-3)}" | bc)
USER_ID=$(( $USER_ID + 1001 ))

/usr/bin/ldapadd -x -D "${ADMIN_DN}" -w "${ADMIN_PASS}" <<LDIF
dn: uid=${NEW_UID},${USER_BASE_DN}
changetype: add
objectClass: person
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: ldapPublicKey
objectClass: posixAccount
objectClass: shadowAccount
objectClass: top
cn: ${NEW_CN}
sn: ${NEW_CN}
uid: ${NEW_UID}
mail: ${NEW_UID}@local.wmftest.net
userPassword: vagrant
uidNumber: ${USER_ID}
gidNumber: ${USER_ID}
homeDirectory: /home/${NEW_UID}
loginShell: /bin/bash

dn: cn=wmf,ou=groups,${BASE_DN}
changetype: modify
add: member
member: uid=${NEW_UID},${USER_BASE_DN}

dn: cn=project-tools,ou=groups,${BASE_DN}
changetype: modify
add: member
member: uid=${NEW_UID},${USER_BASE_DN}
LDIF
