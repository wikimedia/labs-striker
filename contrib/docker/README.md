Striker Docker dev environment
==============================
Striker is a glue application that orchestrates changes in multiple external
services. For development, you can use Docker to setup all the things.

* Striker: http://striker.local.wmftest.net:8080/
* Phabricator: http://phabricator.local.wmftest.net:8081/
* SUL wiki (pretend its meta): http://sulwiki.local.wmftest.net:8082/
* LDAP wiki (pretend its wikitech): http://ldapwiki.local.wmftest.net:8083/
* GitLab: http://gitlab.local.wmftest.net:8084/

The docker-compose and Dockerfile automation take care of the basic
installation and configuration of the various software components needed to
develop and test Striker, but there are some additional configuration steps
that must be performed manually.

First boot
----------
The initial startup of the docker-compose environment will be slow, and very
likely will have some issues that require manual intervention. This is not
ideal obviously, but there is a lot of software to setup and no active
provisioning tool (like Puppet, Chef, Saltstack, etc) to handle state
reconciliation for us.

```console
$ make start tail
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

Save the consumer token and secret token values for use later when we are
setting up Striker.

### Approve OAuth consumers
Approve both consumers at http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthManageConsumers/proposed

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
* Instance shell account name: strikerbot

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
  * Access two-factor authentication (OATH) information for self and others
* Check the "By submitting this application, ..." checkbox

Save the consumer token, consumer secret, access token, and access secret
values for use later when we are setting up Striker.

### Grant StrikerBot the ability to check OATH information

* Log out of the StrikerBot account
* Login as the Admin~ldapwiki account
  * Username: Admin~ldapwiki
  * Password: docker-mediawiki

http://ldapwiki.local.wmftest.net:8083/wiki/Special:UserRights/StrikerBot

Add to groups:
* bot
* oathauth

Setup Phabricator
-----------------
* URL: http://phabricator.local.wmftest.net:8081/
* USERNAME: admin
* PASSWORD: docker-phabricator

### Configure LDAP auth
http://phabricator.local.wmftest.net:8081/auth/config/edit/?provider=PhabricatorLDAPAuthProvider

* Check the "Trust Email Addresses" checkbox
* LDAP Hostname: openldap.local.wmftest.net
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

Copy the API token for use later in configuring the Striker app

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

Setup GitLab
------------
* URL: http://gitlab.local.wmftest.net:8084/
* USERNAME: root
* PASSWORD: docker-gitlab

### Create a StrikerBot bot account
http://gitlab.local.wmftest.net:8084/users/sign_in

* LDAP Username: strikerbot
* Password: strikerbot-docker

### Create API access token for StrikerBot
http://gitlab.local.wmftest.net:8084/-/profile/personal_access_tokens

* Token name: Striker API integration
* Scopes: api

Save the personal access token value for use later when we are setting up
Striker.

### Create public group "toolforge-repos"
http://gitlab.local.wmftest.net:8084/groups/new#create-group-pane

* Group name: toolforge-repos
* Visiblity level: Public

Save the Group ID for use later when we are setting up Striker.

### Make StrikerBot bot account an administrator
http://gitlab.local.wmftest.net:8084/admin/users/strikerbot/edit

Only administrators are allowed to create local accounts for other LDAP users.
The default "root" administrator account can be used to make StrikerBot an
administrator.

* Log out
* Login as root / docker-gitlab
* Visit http://gitlab.local.wmftest.net:8084/admin/users/strikerbot/edit
* Access level: Administrator
* "Save changes"

Setup Striker
-------------
URL: http://striker.local.wmftest.net:8080/

* Edit your .env configuration file:
  * GITLAB_ACCESS_TOKEN = <20 char personal access token>
  * GITLAB_REPO_NAMESPACE_ID = <integer>
  * OAUTH_CONSUMER_KEY = <32 char consumer token>
  * OAUTH_CONSUMER_SECRET = <40 char secret token>
  * PHABRICATOR_TOKEN = api-<28 chars>
  * PHABRICATOR_REPO_ADMIN_GROUP = PHID-PROJ-<20 chars>
  * PHABRICATOR_PARENT_PROJECT = PHID-PROJ-<20 chars>
  * WIKITECH_CONSUMER_TOKEN = <32 char consumer token>
  * WIKITECH_CONSUMER_SECRET = <40 char consumer secret>
  * WIKITECH_ACCESS_TOKEN = <32 char access token>
  * WIKITECH_ACCESS_SECRET = <40 char access secret>
* Load the new settings: `make restart tail`
