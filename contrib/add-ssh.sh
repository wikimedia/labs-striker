#!/usr/bin/env bash
# Add an SSH key to LDAP for local testing.
#
# ** This is hardcoded for the MediaWiki-Vagrant LDAP testing schema **
# ** and not a safe tool to be used with a production LDAP server. **
#
# Usage: add-ssh.sh SHELL_USER_NAME SSH_PUB_KEY

NEW_UID=${1:?SHELL_USER_NAME required}
PUB_KEY=${2:?SSH_PUB_KEY required}
BASE_DN="dc=wmftest,dc=net"
USER_BASE_DN="ou=People,${BASE_DN}"
ADMIN_DN="cn=admin,${BASE_DN}"
ADMIN_PASS="vagrant_admin"

/usr/bin/ldapmodify -x -D "${ADMIN_DN}" -w "${ADMIN_PASS}" <<LDIF
dn: uid=${NEW_UID},${USER_BASE_DN}
changetype: modify
add: sshPublicKey
sshPublicKey: ${PUB_KEY}
LDIF
