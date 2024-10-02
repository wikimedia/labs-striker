<?php
# This file was automatically generated by the MediaWiki 1.36.1
# installer. If you make manual changes, please keep track in case you
# need to recreate them later.
#
# See includes/DefaultSettings.php for all configurable settings
# and their default values, but don't forget to make changes in _this_
# file, not there.
#
# Further documentation for configuration settings may be found at:
# https://www.mediawiki.org/wiki/Manual:Configuration_settings

# Protect against web entry
if ( !defined( 'MEDIAWIKI' ) ) {
	exit;
}

function env( $name, $default = false ) {
	return getenv( $name ) ?: $default;
}

## Uncomment this to disable output compression
# $wgDisableOutputCompression = true;

$wgSitename = "LdapWiki";

## The URL base path to the directory containing the wiki;
## defaults for all runtime URL paths are based off of this.
## For more information on customizing the URLs
## (like /w/index.php/Page_title to /wiki/Page_title) please see:
## https://www.mediawiki.org/wiki/Manual:Short_URL
$wgScriptPath = "/w";

## The protocol and server name to use in fully-qualified URLs
$wgServer = env( "WG_SERVER", "http://ldapwiki.local.wmftest.net:8083" );
$wgCanonicalServer = $wgServer;

## The URL path to static resources (images, scripts, etc.)
$wgResourceBasePath = $wgScriptPath;

## The URL paths to the logo.  Make sure you change this from the default,
## or else you'll overwrite your logo when you upgrade!
$wgLogos = [ '1x' => "$wgResourceBasePath/resources/assets/wiki.png" ];

## UPO means: this is also a user preference option

$wgEnableEmail = true;
$wgEnableUserEmail = true; # UPO

$wgEmergencyContact = "apache@🌻.invalid";
$wgPasswordSender = "apache@🌻.invalid";

$wgEnotifUserTalk = false; # UPO
$wgEnotifWatchlist = false; # UPO
$wgEmailAuthentication = true;

## Database settings
$wgDBtype = "mysql";
$wgDBserver = "mariadb";
$wgDBname = "ldapwiki";
$wgDBuser = "mediawiki";
$wgDBpassword = "mediawiki";

# MySQL specific settings
$wgDBprefix = "";

# MySQL table options to use during installation or update
$wgDBTableOptions = "ENGINE=InnoDB, DEFAULT CHARSET=binary";

# Shared database table
# This has no effect unless $wgSharedDB is also set.
$wgSharedTables[] = "actor";

## Shared memory settings
$wgMainCacheType = CACHE_ACCEL;
$wgMemCachedServers = [];

## To enable image uploads, make sure the 'images' directory
## is writable, then set this to true:
$wgEnableUploads = true;
$wgUseImageMagick = true;
$wgImageMagickConvertCommand = "/usr/bin/convert";

# InstantCommons allows wiki to use images from https://commons.wikimedia.org
$wgUseInstantCommons = true;

# Periodically send a pingback to https://www.mediawiki.org/ with basic data
# about this MediaWiki instance. The Wikimedia Foundation shares this data
# with MediaWiki developers to help guide future development efforts.
$wgPingback = true;

## If you use ImageMagick (or any other shell command) on a
## Linux server, this will need to be set to the name of an
## available UTF-8 locale. This should ideally be set to an English
## language locale so that the behaviour of C library functions will
## be consistent with typical installations. Use $wgLanguageCode to
## localise the wiki.
$wgShellLocale = "C.UTF-8";

## Set $wgCacheDirectory to a writable directory on the web server
## to make your wiki go slightly faster. The directory should not
## be publicly accessible from the web.
#$wgCacheDirectory = "$IP/cache";

# Site language code, should be one of the list in ./languages/data/Names.php
$wgLanguageCode = "en";

$wgSecretKey = "vJ5MiFZ8jD2NPqTKJ6eORCkXHSgRLK33Fg2yTImeoxBGffoFmmQhmkIi2ZJgJ1cy";

# Changing this will log out all existing sessions.
$wgAuthenticationTokenVersion = "1";

# Site upgrade key. Must be set to a string (default provided) to turn on the
# web installer while LocalSettings.php is in place
# $wgUpgradeKey = "1f199a1c9aeaf0a4";

## For attaching licensing metadata to pages, and displaying an
## appropriate copyright notice / icon. GNU Free Documentation
## License and Creative Commons licenses are supported so far.
$wgRightsPage = ""; # Set to the title of a wiki page that describes your license/copyright
$wgRightsUrl = "https://creativecommons.org/licenses/by-sa/4.0/";
$wgRightsText = "Creative Commons Attribution-ShareAlike";
$wgRightsIcon = "$wgResourceBasePath/resources/assets/licenses/cc-by-sa.png";

# Path to the GNU diff3 utility. Used for conflict resolution.
$wgDiff3 = "/usr/bin/diff3";

## Default skin: you can change the default skin. Use the internal symbolic
## names, ie 'vector', 'monobook':
$wgDefaultSkin = "vector";

# Enabled skins.
# The following skins were automatically enabled:
wfLoadSkin( 'Timeless' );
wfLoadSkin( 'Vector' );


# Enabled extensions. Most of the extensions are enabled by adding
# wfLoadExtension( 'ExtensionName' );
# to LocalSettings.php. Check specific extension documentation for more details.
# The following extensions were automatically enabled:
wfLoadExtension( 'CodeEditor' );
wfLoadExtension( 'InputBox' );
wfLoadExtension( 'Interwiki' );
wfLoadExtension( 'MultimediaViewer' );
wfLoadExtension( 'ParserFunctions' );
wfLoadExtension( 'Scribunto' );
wfLoadExtension( 'SyntaxHighlight_GeSHi' );
wfLoadExtension( 'TemplateData' );
wfLoadExtension( 'TitleBlacklist' );
wfLoadExtension( 'WikiEditor' );


# End of automatically generated settings.
# Add more configuration options below.

wfLoadExtension( 'OAuth' );
$wgMWOAuthSecureTokenTransfer = false;
$wgOAuthSecretKey = '292ed299345a01c1c0520b60f628c01ea817a0b3372b89dbb7637a2f678d018a';
$wgGroupPermissions["sysop"]["mwoauthmanageconsumer"] = true;
$wgGroupPermissions["user"]["mwoauthproposeconsumer"] = true;
$wgGroupPermissions["user"]["mwoauthupdateownconsumer"] = true;
$wgOAuthGroupsToNotify = [ "sysop" ];
$wgOAuth2PrivateKey = <<<EOK
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAraLb9UGlKxhKpfsW/DLjiFG/gHkywfcdpTDxpHgGi3q8ZZHl
1fGzhnBt4S0sKMqJMR/PjVcZrsQvM+uGKG7NZ1htJAWw+s4/cQjFSCHayozOG5QT
aGlue8u7SwCwMKDIlPFt1IXrsP6glEenZbSZntjRnVx2CrVRcSxiIJYkM8IrQxz+
69Svh8cGhyulOXYuqAhU10lzteFdMp9iimKf9R+cFyuLJ7jXu14hK4GnG1j08orc
H3Q7LmEFzRB3AFlxS+HoV0kD0O6wj6c9JABDsOZXCcjFHQOQI4GVEE040NtcdK5I
CbELOnI50cQ1Wr/H/Mxqg6hs/o3suDzngereCwIDAQABAoIBABj2hwT1kRdnAKRo
Ot+7OTcJ+awwwHleW6a6KKNqlhZLaPZ5ST++5f53/3QWGHks1Rh46E/7q7eSgO7H
95usgl9POTGql80XBcvsZOB/7YKdR6xzV271aWrm2WBpEuuK0guHwjCBqGbj1JY8
zvYyRrutlEU5W8ciVjkdFmZ073N5RDulAitFGEAJwyfko8dpr1Z1FOmIS9lU8qip
AGBozZEsza73s1IDJx3BMcRQl8rfuuG4L65bSd06w6Zy2VPyI6Xoe2PMKYfgaWiB
WNdkwesSufWeB4fCsWV24Ww4hQQEHRfl1e+0/0iXLtN4BzIWeShVCy2VIncsHX6e
+YamqaECgYEA0uP/39YiLQ/u2K1awdXMJVn+JI4Wqaoy+CdAWIR+twljBgF4ILvC
R+pv47YJCeid4L3uzQlcOh0LU9o9dHQ9fFuwHvksulu+B5yow5Kz8SRFiR9urhfI
+4VEvISbjzbRAbMr1Rrq9dNbQgQBC97/YLiPTloV8XSsYuWWkRMtQgMCgYEA0sbf
A8xNgMC3G34z6AHBp3zC9v5yYolLtj2JgW0NNaaa3yAK16ed2MV0zRhgGnfrcu/I
9fdPevC2j6BgI6x03ppVEqp4vTPtn2oko9MdqY3AdQEe/Xxkcillr6bB4Hiy482o
HJjxsUN71y53SLntM2dIewZL5HZpQ4pBQnH++VkCgYBWtzHLlH1REjAgIIglFAhx
g2OhHFvtP/LdXyZyP2jrUozJN2lx7EKi159SftOQo3nno7HB1Yt6yd6SiDak3/c4
X2s4ETV3G6oz7xLl+DjNeyCslaQpKdaWteHhspVUejHPBSGM6xiaJGJt7r+PZg6U
cs9aZGiJdHQ95jHXTY9aiQKBgQDHHxtmgiahwO37KiGtR6OEL+gb4Mt87Um6c64o
uDYnfiqHKcU0cGQ9emTasPFxb+Ld5UuLmsTaVveQ/ih06yJJfbFq/eMskxckZ+kP
X42BNaognxuAy3g1JYisBTTZdA1ECnCL+60xEpi28227JfLBggxGNO+TeI3/QWhf
dkQzmQKBgQCeXkT6DYI2jQdOyB0V3jAo75NvIvj2ljMJU6PFkFonYrrd05UHXcIu
XuzHriiykVhayEISPlgcKj1lmR6LC1OhLA+Xpf2ma1GU7bIMNVsgVU0kaZTC9Ur3
BOlbXnjr7Aygo474QJim60TZg0z7ZHv+5DmbKBEe9AO4pri/n/qKCg==
-----END RSA PRIVATE KEY-----
EOK;
$wgOAuth2PublicKey = <<<EOK
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAraLb9UGlKxhKpfsW/DLj
iFG/gHkywfcdpTDxpHgGi3q8ZZHl1fGzhnBt4S0sKMqJMR/PjVcZrsQvM+uGKG7N
Z1htJAWw+s4/cQjFSCHayozOG5QTaGlue8u7SwCwMKDIlPFt1IXrsP6glEenZbSZ
ntjRnVx2CrVRcSxiIJYkM8IrQxz+69Svh8cGhyulOXYuqAhU10lzteFdMp9iimKf
9R+cFyuLJ7jXu14hK4GnG1j08orcH3Q7LmEFzRB3AFlxS+HoV0kD0O6wj6c9JABD
sOZXCcjFHQOQI4GVEE040NtcdK5ICbELOnI50cQ1Wr/H/Mxqg6hs/o3suDzngere
CwIDAQAB
-----END PUBLIC KEY-----
EOK;

wfLoadExtension( 'LdapAuthentication' );
$wgAuthManagerAutoConfig['primaryauth'] += [
	LdapPrimaryAuthenticationProvider::class => [
		'class' => LdapPrimaryAuthenticationProvider::class,
		'args' => [ [
			'authoritative' => true, // don't allow local non-LDAP accounts
		] ],
		'sort' => 50, // must be smaller than local pw provider
	],
];

$wgLDAPDomainNames = [ 'ldap' ];
$wgLDAPServerNames = [ 'ldap' => 'openldap.local.wmftest.net' ];
$wgLDAPEncryptionType = [ 'ldap' => 'clear' ];

$wgLDAPProxyAgent =  [ 'ldap' => 'cn=proxyagent,dc=wmftest,dc=net' ];
$wgLDAPProxyAgentPassword =  [ 'ldap' => 'readonly' ];

$wgLDAPSearchAttributes = [ 'ldap' => 'cn:caseExactMatch:' ];
$wgLDAPBaseDNs = [ 'ldap' => 'dc=wmftest,dc=net' ];
$wgLDAPUserBaseDNs = [ 'ldap' => 'ou=People,dc=wmftest,dc=net' ];

$wgLDAPWriterDN = [ 'ldap' => 'cn=writer,dc=wmftest,dc=net' ];
$wgLDAPWriterPassword = [ 'ldap' => 'docker_writer' ];

$wgLDAPWriteLocation = [ 'ldap' => 'ou=People,dc=wmftest,dc=net' ];
$wgLDAPAddLDAPUsers = [ 'ldap' => true ];
$wgLDAPUpdateLDAP = [ 'ldap' => true ];
$wgLDAPPasswordHash = [ 'ldap' => 'clear' ];

// 'invaliddomain' is set to true so that mail password options
// will be available on user creation and password mailing
$wgLDAPMailPassword = [ 'ldap' => true, 'invaliddomain' => true ];
$wgLDAPPreferences = [ 'ldap' => [ 'email' => 'mail' ] ];
$wgLDAPUseFetchedUsername = [ 'ldap' => true ];
$wgLDAPLowerCaseUsernameScheme = [ 'ldap' => false, 'invaliddomain' => false ];
$wgLDAPLowerCaseUsername = [ 'ldap' => false, 'invaliddomain' => false ];

$wgLDAPLockOnBlock = true;
$wgLDAPLockPasswordPolicy = 'cn=disabled,ou=ppolicies,dc=wmftest,dc=net';

// Log all the things!
$wgLDAPDebug = 3;
$wgDebugLogGroups['ldap'] = "php://stderr";

// Shortest password a user is allowed to login using. Notice that 1 is the
// minimum so that when using a local domain, local users cannot login as
// domain users (as domain user's passwords are not stored)
$wgPasswordPolicy['default']['MinimalPasswordLength'] = 1;

wfLoadExtension( 'OpenStackManager' );
$wgOpenStackManagerLDAPDomain = "ldap";
$wgOpenStackManagerLDAPUser = "cn=writer,dc=wmftest,dc=net";
$wgOpenStackManagerLDAPUserPassword = "docker_writer";

$wgDebugLogFile = "php://stderr";

error_reporting( -1 );
ini_set( 'display_errors', 1 );
$wgMaxShellMemory = 1024 * 512;
$wgShowExceptionDetails = true;
$wgDevelopmentWarnings = true;
$wgDebugDumpSql = true;
$wgResourceLoaderStorageEnabled = false;
$wgDebugProfiling = false;

$wgAllowUserJs = true;
$wgAllowUserCss = true;
$wgEnableJavaScriptTest = true;

// Eligibility for autoconfirmed group
$wgAutoConfirmAge = 3600 * 24; // one day
$wgAutoConfirmCount = 5; // five edits

# dynamic thumbnail generation
$wgThumbnailScriptPath = false;
$wgGenerateThumbnailOnParse = false;

# pretty urls
$wgScriptPath = "/w";
$wgArticlePath = "/wiki/$1";
