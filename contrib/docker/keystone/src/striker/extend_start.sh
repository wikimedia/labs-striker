#!/bin/bash
set -euxo pipefail
echo "== Striker kolla_keystone_bootstrap ==" >&2

CONF=/var/lib/kolla/config_files/src/striker
DTU=/usr/local/bin/dtu

: ${KEYSTONE_DB_HOST:=keystone_db}
export KEYSTONE_DB_HOST

echo "* Generating config from templates" >&2
$DTU -o /etc/keystone/keystone.conf $CONF/keystone.conf.j2
$DTU -o /etc/keystone/admin-openrc $CONF/admin-openrc.j2

echo "* Sourcing config" >&2
. /etc/keystone/admin-openrc

echo "* Initializing fernet tokens" >&2
install -d -o root -g keystone -m 770 /etc/keystone/fernet-keys
runuser -u keystone -- keystone-manage fernet_setup \
  --keystone-user keystone \
  --keystone-group keystone

echo "* Initializing database schema"
while ! keystone-manage db_sync; do
  echo "! database schema initialization failed; retrying in 5 seconds..." >&2
  sleep 5
done

echo "* Initializing service catalog"
runuser -u keystone -- keystone-manage bootstrap \
  --bootstrap-username admin \
  --bootstrap-password ${KEYSTONE_ADMIN_PASSWORD} \
  --bootstrap-project-name admin \
  --bootstrap-role-name admin \
  --bootstrap-service-name keystone \
  --bootstrap-admin-url http://keystone:5000 \
  --bootstrap-internal-url http://localhost:5000 \
  --bootstrap-public-url ${KEYSTONE_PUBLIC_URL:-http://keystone:5000} \
  --bootstrap-region-id ${KEYSTONE_REGION:-Docker}

echo "* Starting Apache" >&2
APACHE_CONFDIR=
. /usr/local/bin/kolla_httpd_setup
ARGS="-DFOREGROUND"

echo "* Forking post-start bootstrap script" >&2
$CONF/post_start.sh &
