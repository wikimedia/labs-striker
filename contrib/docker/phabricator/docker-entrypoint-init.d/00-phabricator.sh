#!/bin/bash

/opt/bitnami/phabricator/bin/config set phabricator.base-uri 'http://phabricator.local.wmftest.net:8081'
/opt/bitnami/phabricator/bin/config set ui.header-color 'red'
/opt/bitnami/phabricator/bin/config set ui.footer-items '[{"name":"Striker
local dev stack"}]'

# Load custom Wikimedia extensions
/opt/bitnami/phabricator/bin/config set load-libraries '["/srv/phabricator-extensions"]'

/opt/bitnami/phabricator/bin/config set security.require-https 'false'
/opt/bitnami/phabricator/bin/config set phabricator.developer-mode 'true'
/opt/bitnami/phabricator/bin/config set darkconsole.enabled 'true'
/opt/bitnami/phabricator/bin/config set diffusion.allow-http-auth 'true'

/opt/bitnami/phabricator/bin/config set auth.require-approval 'false'
/opt/bitnami/phabricator/bin/config set policy.allow-public 'true'

/opt/bitnami/phabricator/bin/auth unlock
