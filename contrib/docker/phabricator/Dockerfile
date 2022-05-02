FROM docker.io/bitnami/phabricator:2021

ENV PHABRICATOR_USERNAME=admin \
    PHABRICATOR_PASSWORD=docker-phabricator \
    PHABRICATOR_EMAIL=ldapadmin@local.wmftest.net \
    PHABRICATOR_FIRSTNAME=Admin \
    PHABRICATOR_LASTNAME=User \
    PHABRICATOR_HOST=phabricator.local.wmftest.net \
    MARIADB_HOST=mariadb \
    PHABRICATOR_DATABASE_ADMIN_USER=root \
    PHABRICATOR_DATABASE_ADMIN_PASSWORD=root \
    PHABRICATOR_ENABLE_HTTPS="false" \
    PHABRICATOR_EXTERNAL_HTTP_PORT_NUMBER=8081 \
    APACHE_HTTP_PORT_NUMBER=8081

COPY docker-entrypoint-init.d /docker-entrypoint-init.d/

# Add Wikimedia custom add-ons
USER root
RUN git clone https://github.com/wikimedia/phabricator-extensions /srv/phabricator-extensions
USER 1001
