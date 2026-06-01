Striker Docker dev environment
==============================
Striker is a glue application that orchestrates changes in multiple external
services. For development, you can use Docker to setup all the things.

* Striker: http://striker.local.wmftest.net:8080/
* Phabricator: http://phabricator.local.wmftest.net:8081/
* SUL wiki (pretend its meta): http://sulwiki.local.wmftest.net:8082/
* LDAP wiki (pretend its wikitech): http://ldapwiki.local.wmftest.net:8083/
* GitLab: http://gitlab.local.wmftest.net:8084/
* Bitu: http://idm.local.wmftest.net:8085/

The docker-compose and Dockerfile automation take care of the basic
installation and configuration of the various software components needed to
develop and test Striker, but there are some additional configuration steps
that must be performed manually.

Using Podman
-----------------------
Using [Podman](https://podman.io) as a drop-in replacement for Docker is mostly
supported, however there are a few catches to be aware of.

* It is necessary to run `docker-compose` directly, which means you will need
  to set `$DOCKER_HOST` according to the output of `podman machine start`.
* `docker-compose run --build` and similar will tag its images as
  `docker.io/striker/<service>`, while `podman build --tag striker/<service>`
  will tag images as `localhost/striker/<service>`. This will then cause issues
  when running the compose file, as the older `localhost`-prefixed images will
  take precedence over the new `docker.io`-prefixed images.
* On macOS under Podman, it may be necessary to add the following to
  `~/.config/containers/containers.conf`, especially if you witness a
  segfault from esbuild when attempting to run `make build`:
  ```toml
  [machine]
  rosetta = true
  ```
  You will need to run `podman machine stop && podman machine start` after
  making this change.

First boot
----------
The initial startup of the docker-compose environment will be slow, and very
likely will have some issues that require manual intervention. This is not
ideal obviously, but there is a lot of software to setup and no active
provisioning tool (like Puppet, Chef, Saltstack, etc) to handle state
reconciliation for us.

```console
$ make build start tail
 So much stuff scrolls by...
 Still scrolling...
 Will it ever stop?
 It should, but be on the lookout for repeating loops
 Eventually (~1-3 minutes) things should stop scrolling
 ^c
$ make init
 More scrolling...
 This should only take a few seconds...
```

If you try to load http://striker.local.wmftest.net:8080/ and get a connection
refused error, try restarting the `striker` container now that everything else
is up and running.

Setup SUL wiki
----------------
* URL: http://sulwiki.local.wmftest.net:8082/
* USERNAME: Admin
* PASSWORD: docker-mediawiki

This wiki is used as a stand-in for the functionality of metawiki in the
Striker stack. We need to create and approve several OAuth consumer
registrations here that will be used by other applications in the stack.

### Create OAuth consumer for Phabricator
http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthConsumerRegistration/propose/oauth1a

* Application name: Phabricator
* Application description: Phabricator login
* OAuth "callback" URL: http://phabricator.local.wmftest.net:8081/auth/login/mediawiki:sulwiki.local.wmftest.net/
* Check the 'Allow consumer to specify a callback in requests and use
  "callback" URL above as a required prefix.' checkbox
* Types of grants being requested: "User identity verification only with
  access to real name and email address, no ability to read pages or act on
  a user's behalf."
* Check the "By submitting this application, ..." checkbox

Save the consumer token and secret token values for use later when we are
setting up Phabricator.

### Create OAuth consumer for Striker
http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthConsumerRegistration/propose/oauth1a

* Application name: Toolforge
* Application description: Toolforge console
* OAuth callback URL: http://striker.local.wmftest.net:8080
* Check the 'Allow consumer to specify a callback in requests and use
  "callback" URL above as a required prefix.' checkbox.
* Types of grants being requested: "User identity verification only with access
  to real name and email address, no ability to read pages or act on a user's
  behalf."
* Check the "By submitting this application, ..." checkbox

Update your `.env` file with the consumer token and secret token:
```sh
OAUTH_CONSUMER_KEY = <32 char consumer token>
OAUTH_CONSUMER_SECRET = <40 char secret token>
```

### Create OAuth consumer for Bitu
http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthConsumerRegistration/propose/oauth1a

* Application name: Bitu
* Application description: Bitu Integration
* OAuth callback URL: http://bitu.local.wmftest.net:8085/complete/mediawiki
* Types of grants being requested: "User identity verification only with access
  to real name and email address, no ability to read pages or act on a user's
  behalf."
* Check the "By submitting this application, ..." checkbox

Save the consumer token and secret token values for use later when we are
setting up Bitu.

Update your `.env` file with the consumer token and secret token:
```sh
BITU_SULWIKI_CONSUMER_TOKEN = <32 char consumer token>
BITU_SULWIKI_CONSUMER_SECRET = <40 char secret token>
```

### Approve OAuth consumers
Approve all three consumers at http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthManageConsumers/proposed

Setup LDAP wiki
---------------
* URL: http://ldapwiki.local.wmftest.net:8083/
* USERNAME: Admin
* PASSWORD: admin

This wiki is used as a stand-in for the functionality of wikitech in the
Striker stack.

### Create StrikerBot account
http://ldapwiki.local.wmftest.net:8083/wiki/Special:CreateAccount

* Username: StrikerBot
* Password: strikerbot-docker
* Email address: strikerbot@local.wmftest.net

### Create StrikerBot owner-only consumer
http://ldapwiki.local.wmftest.net:8083/wiki/Special:OAuthConsumerRegistration/propose/oauth1a

* Application name: Striker
* Application description: Allow Striker to auth as StrikerBot account for various wiki interactions including 2fa validation.
* Check the "This consumer is for use only by StrikerBot." checkbox
* Select grants:
  * Basic rights
  * High-volume (bot) access
  * Edit existing pages
  * Edit protected pages
  * Create, edit, and move pages
  * Upload new files
  * Upload, replace, and move files
  * Rollback changes to pages
  * Block and unblock users
  * Protect and unprotect pages
  * Send email to other users
  * Access private information
* Check the "By submitting this application, ..." checkbox

Update your `.env` file with all four tokens:
```sh
WIKITECH_CONSUMER_TOKEN = <32 char consumer token>
WIKITECH_CONSUMER_SECRET = <40 char consumer secret>
WIKITECH_ACCESS_TOKEN = <32 char access token>
WIKITECH_ACCESS_SECRET = <40 char access secret>
```

### Grant StrikerBot the bot right

* Log out of the StrikerBot account
* Login as the Admin~ldapwiki account
  * Username: Admin~ldapwiki
  * Password: docker-mediawiki

http://ldapwiki.local.wmftest.net:8083/wiki/Special:UserRights/StrikerBot

Add to groups:
* bot

Setup Phabricator
-----------------
* URL: http://phabricator.local.wmftest.net:8081/
* USERNAME: admin
* PASSWORD: docker-phabricator

### Configure LDAP auth
http://phabricator.local.wmftest.net:8081/auth/config/edit/?provider=PhabricatorLDAPAuthProvider

* Check the "Trust Email Addresses" checkbox
* LDAP Hostname: openldap.local.wmftest.net
* LDAP Port: 1389
* Base Distinguished Name: ou=People,dc=wmftest,dc=net
* Search Attributes: cn
* Check the "Always Search" checkbox

### Connect Phabricator admin user with ldapwiki Admin account
http://phabricator.local.wmftest.net:8081/auth/link/2/

* LDAP Username: Admin
* LDAP Password: admin
* Click "Link Accounts"
* Click "Confirm Account Link"

### Configure a MediaWiki auth provider
http://phabricator.local.wmftest.net:8081/auth/config/edit/?provider=PhabricatorMediaWikiAuthProvider

* Check the "Trust Email Addresses" checkbox
* MediaWiki Instance Name: sulwiki.local.wmftest.net
* MediaWiki Base URI: http://sulwiki.local.wmftest.net:8082/w

http://phabricator.local.wmftest.net:8081/auth/config/edit/3/
* Copy the "consumer token" value from the grant made at sulwiki to the "Consumer Key" field.
* Copy the "secret token" value from the grant made at sulwiki to the "Secret Key" field.

### Connect Phabricator admin user with sulwiki Admin account
http://phabricator.local.wmftest.net:8081/auth/link/3/

### Create a StrikerBot bot account
http://phabricator.local.wmftest.net:8081/people/new/bot/

* Username: StrikerBot
* Real Name: Toolforge helper
* Email: striker@local.wmftest.net

### Generate a Conduit API token for StrikerBot
http://phabricator.local.wmftest.net:8081/settings/user/StrikerBot/page/apitokens/

Update your `.env` file with the API token:
```sh
PHABRICATOR_TOKEN = api-<28 chars>
```

### Create a "Repository-Admins" project
http://phabricator.local.wmftest.net:8081/project/edit/form/default/

* Name: Repository-Admins
* Icon: Group
* Color: Violet
* Initial Members: admin, StrikerBot
* Editable By: Project Members
* Joinable By: Administrators

### Configure permissions for diffusion repo management
http://phabricator.local.wmftest.net:8081/applications/edit/PhabricatorDiffusionApplication/

* Default Edit Policy: Repository-Admins
* Default Push Policy: Repository-Admins
* Can Create Repositories: Repository-Admins

### Lookup PHID of "Repository-Admins" group
http://phabricator.local.wmftest.net:8081/project/profile/1/

* Click "View All" in the "Recent Activity" pane
* Copy the PHID-PROJ- value from the URL.

Update your `.env` file:
```sh
PHABRICATOR_REPO_ADMIN_GROUP = PHID-PROJ-<20 chars>
```

### Create a "Tools" project
http://phabricator.local.wmftest.net:8081/project/edit/form/default/

* Name: Tools
* Icon: Umbrella
* Color: Blue
* Editable By: All Users
* Joinable By: All Users

### Lookup PHID of "Tools" group
http://phabricator.local.wmftest.net:8081/project/profile/2/

* Click "View All" in the "Recent Activity" pane
* Copy the PHID-PROJ- value from the URL.

Update your `.env` file:
```sh
PHABRICATOR_PARENT_PROJECT = PHID-PROJ-<20 chars>
```

Setup GitLab
------------
### Create a StrikerBot bot account
http://gitlab.local.wmftest.net:8084/users/sign_in

* LDAP Username: strikerbot
* Password: strikerbot-docker

### Create API access token for StrikerBot
http://gitlab.local.wmftest.net:8084/-/profile/personal_access_tokens

* Token name: Striker API integration
* Scopes: api

Update your `.env` file with the personal access token:
```sh
GITLAB_ACCESS_TOKEN = glpat-<20 char personal access token>
```

### Create public group "toolforge-repos"
http://gitlab.local.wmftest.net:8084/groups/new#create-group-pane

* Group name: toolforge-repos
* Visiblity level: Public

Update your `.env` file with the Group ID:
```sh
GITLAB_REPO_NAMESPACE_ID = <integer>
```

### Make StrikerBot bot account an administrator
Only administrators are allowed to create local accounts for other LDAP users.
The default "root" administrator account can be used to make StrikerBot an
administrator.

* Log out
* Log in using the "Standard" authentication provider
  * URL: http://gitlab.local.wmftest.net:8084/
  * USERNAME: root
  * PASSWORD: docker-git-lab
* Visit http://gitlab.local.wmftest.net:8084/admin/users/strikerbot/edit
* Access level: Administrator
* "Save changes"

Setup Striker
-------------
URL: http://striker.local.wmftest.net:8080/
USERNAME: admin
PASSWORD: admin

* Save the `.env` file
* Load the new settings: `make restart tail`
