#!/bin/bash
set -euxo pipefail
echo "== Striker post-start bootstrapping ==" >&2

until curl -If 'http://keystone:5000/v3/' 2>&1 >/dev/null; do
  sleep 1
done

echo "* Sourcing config" >&2
. /etc/keystone/admin-openrc

runuser -u keystone -- /usr/bin/env | sort

runuser -u keystone -- openstack project create --or-show \
  --description "Service Project" \
  service

runuser -u keystone -- openstack project create --or-show \
  --description "Toolforge" \
  tools

runuser -u keystone -- openstack role create --or-show service
runuser -u keystone -- openstack role create --or-show _member_
runuser -u keystone -- openstack role create --or-show admin
runuser -u keystone -- openstack role create --or-show observer
runuser -u keystone -- openstack role create --or-show projectadmin
runuser -u keystone -- openstack role create --or-show user

runuser -u keystone -- openstack role add --user admin --project tools admin
