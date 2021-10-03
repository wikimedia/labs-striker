OpenStack Keystone
==================

An OpenStack Keystone service for developing Striker.

Includes several custom libraries developed at Wikimedia to extend Keystone.
These libraries are copied from the Wikimedia ops/puppet.git repo which hosts
their canonical versions.

This image also includes a couple of hacks against the upstream Keystone
project in the form of files which overwrite the upstream versions:
* src/usr/lib/python3/dist-packages/keystone/api/projects.py - preserve an
  ancient Keystone legacy behavior of human-readable project ids.
* src/usr/lib/python3/dist-packages/keystone/cmd/bootstrap.py - comment out
  identity provider checks which do not work with the LDAP backend. This has
  been WONTFIX'ed upstream
  (<https://bugs.launchpad.net/keystone/+bug/1643301>) because use of LDAP in
  this way is now actively discouraged.

Inspiration from:
* https://blog.oddbit.com/post/2019-06-07-running-keystone-with-docker-c/
* https://github.com/CCI-MOC/flocx-keystone-dev
* https://adam.younglogic.com/2019/12/official-tripleo-keystone-images/
* https://hub.docker.com/r/kolla/ubuntu-binary-keystone/tags
* https://docs.openstack.org/kolla/latest/admin/kolla_api.html

There are some ugly hacks in here that could be removed by setting up an
additional OpenStack domain for the ldap auth bits. See
https://osm.etsi.org/gitlab/osm/devops/-/blob/master/docker/Keystone/LDAP.md
for inspiration.
