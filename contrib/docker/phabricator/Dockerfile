FROM docker.io/bitnami/phabricator:2021

ENV PHABRICATOR_USERNAME=admin \
    PHABRICATOR_PASSWORD=docker-phabricator \
    PHABRICATOR_EMAIL=ldapadmin@local.wmftest.net \
    PHABRICATOR_FIRSTNAME=Admin \
    PHABRICATOR_LASTNAME=User \
    PHABRICATOR_HOST=phabricator.local.wmftest.net \
    PHABRICATOR_URI=http://phabricator.local.wmftest.net:8081 \
    MARIADB_HOST=mariadb \
    PHABRICATOR_DATABASE_ADMIN_USER=root \
    PHABRICATOR_DATABASE_ADMIN_PASSWORD=root \
    PHABRICATOR_ENABLE_HTTPS="false" \
    PHABRICATOR_EXTERNAL_HTTP_PORT_NUMBER=8081 \
    APACHE_HTTP_PORT_NUMBER=8081

COPY docker-entrypoint-init.d /docker-entrypoint-init.d/

# Add Wikimedia custom add-ons
USER root
RUN git clone https://gitlab.wikimedia.org/repos/phabricator/extensions /srv/phabricator-extensions
USER 1001

# Apache config hack for Docker+Apple Silicon+AMD64 emulation
# https://web.archive.org/web/20221205115651/https://github.com/bitnami/bitnami-docker-wordpress/issues/316
RUN echo 'Mutex posixsem' >>/opt/bitnami/apache2/conf/httpd.conf
