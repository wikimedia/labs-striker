Striker Docker dev environment
==============================
Striker is a glue application that orchestrates changes in multiple external
services. For development, you can use Docker to setup all the things.

* Striker: http://striker.local.wmftest.net:8080/
* Phabricator: http://phabricator.local.wmftest.net:8081/
* SUL wiki (pretend its meta): http://sulwiki.local.wmftest.net:8082/
* LDAP wiki (pretend its wikitech): http://ldapwiki.local.wmftest.net:8083/

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
http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthConsumerRegistration/propose

* Application name: Phabricator
* Application description: Phabricator login
* OAuth "callback" URL: http://phabricator.local.wmftest.net:8081/auth/login/mediawiki:sulwiki/
* Check the 'Allow consumer to specify a callback in requests and use
  "callback" URL above as a required prefix.' checkbox
* Types of grants being requested: "User identity verification only with
  access to real name and email address, no ability to read pages or act on
  a user's behalf."
* Check the "By submitting this application, ..." checkbox

Save the consumer token and secret token values for use later when we are
setting up Phabricator.

### Create OAuth consumer for Striker
http://sulwiki.local.wmftest.net:8082/wiki/Special:OAuthConsumerRegistration/propose

* Application name: Toolforge
* Application description: Toolforge console
* OAuth callback URL: http://striker.local.wmftest.net:8080
* Check the 'Allow consumer to specify a callback in requests and use
  "callback" URL above as a required prefix.' checkbox.
* Contact email address: admin@local.wmftest.net
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
http://ldapwiki.local.wmftest.net:8083/wiki/Special:OAuthConsumerRegistration/propose

* Application name: Striker
* Application description: Allow Striker to auth as StrikerBot account for various wiki interactions including 2fa validation.
* Check the "This consumer is for use only by StrikerBot." checkbox
* Select grants:
  * Basic rights
  * High-volume editing
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

This might fail with cryptic errors and stack traces. If it does that is no
big deal, but you may have a more difficult time testing features of Striker
which involve searching for Phabricator users based on their SUL account
information.

FIXME: figure out why "Expected 'oauth_callback_confirmed' to be 'true'!" is
still happening after fixing the vendor deps...

### Create a "striker" bot account
http://phabricator.local.wmftest.net:8081/people/new/bot/

* Username: striker
* Real Name: Toolforge helper
* Email: striker@local.wmftest.net

### Generate a Conduit API token for "striker"
http://phabricator.local.wmftest.net:8081/settings/user/striker/page/apitokens/

Copy the API token for use later in configuring the Striker app

### Create a "Repository-Admins" project
http://phabricator.local.wmftest.net:8081/project/edit/form/default/

* Name: Repository-Admins
* Icon: Group
* Color: Violet
* Initial Members: admin, striker
* Editable By: Project Members
* Joinable By: Administrators

### Configure permissions for diffusion repo management
http://phabricator.local.wmftest.net:8081/applications/edit/PhabricatorDiffusionApplication/

* Default Edit Policy: Repository-Admins
* Default Push Policy: Repository-Admins
* Can Create Repositories: Repository-Admins

### Lookup PHID of "Repository-Admins" group
http://phabricator.local.wmftest.net:8081/project/profile/1/

* Click "View All"
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

* Click "View All"
* Copy the PHID-PROJ- value from the URL.

Setup Striker
-------------
URL: http://striker.local.wmftest.net:8080/

* Copy contrib/docker/striker.ini to the root of the project.
* Add these settings to the `[oauth]` section:
  * CONSUMER_KEY = <32 char consumer token>
  * CONSUMER_SECRET = <40 char secret token>
* Add these settings to the `[phabricator]` section:
  * TOKEN = api-<28 chars>
  * REPO_ADMIN_GROUP = PHID-PROJ-<20 chars>
  * PARENT_PROJECT = PHID-PROJ-<20 chars>
* Add these settings to the `[wikitech]` section:
  * CONSUMER_TOKEN = <32 char consumer token>
  * CONSUMER_SECRET = <40 char consumer secret>
  * ACCESS_TOKEN = <32 char access token>
  * ACCESS_SECRET = <40 char access secret>

* Load the new settings: `docker-compose restart striker`
