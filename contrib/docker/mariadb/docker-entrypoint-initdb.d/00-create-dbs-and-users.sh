#!/bin/bash
set -euxo pipefail

# XXX: The [ -x ... ] test in docker-entrypoint.sh seems to think all *.sh
# scripts are executable for currently unknown reasons.
. /docker-entrypoint.sh
SOCKET="$(mysql_get_config 'socket' 'mysqld')"

striker_create_db() {
	local DB=$1

	mysql_note "Creating database ${DB}"
	docker_process_sql --database=mysql <<-EOSQL
		CREATE DATABASE IF NOT EXISTS \`$DB\`;
	EOSQL
}

striker_create_user() {
	local USER=$1
	local PASSWORD=$2

	mysql_note "Creating user ${USER}"
	local userPasswordEscaped
	userPasswordEscaped=$( docker_sql_escape_string_literal "${PASSWORD}" )
	docker_process_sql --database=mysql --binary-mode <<-EOSQL
		SET @@SESSION.SQL_MODE=REPLACE(@@SESSION.SQL_MODE, 'NO_BACKSLASH_ESCAPES', '');
		CREATE USER IF NOT EXISTS '$USER'@'%' IDENTIFIED BY '$userPasswordEscaped';
	EOSQL

	if [ -n "$3" ]; then
		local DB=$3
		mysql_note "Giving user ${USER} access to schema ${DB}"
		docker_process_sql --database=mysql <<-EOSQL
			GRANT ALL ON \`${DB//_/\\_}\`.* TO '$USER'@'%';
		EOSQL
	fi
}


striker_create_db "keystone"
striker_create_user "keystone" "keystone" "keystone"

striker_create_db "ldapwiki"
striker_create_user "mediawiki" "mediawiki" "ldapwiki"

striker_create_db "sulwiki"
striker_create_user "mediawiki" "mediawiki" "sulwiki"

striker_create_db "striker"
striker_create_user "striker" "striker" "striker"
