ARG KEYSTONE_IMAGE_TAG=2023.1-debian-bullseye
FROM quay.io/openstack.kolla/keystone:${KEYSTONE_IMAGE_TAG}

RUN set -eux; \
    apt-get clean && apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --yes --no-install-recommends \
      python3-mwclient \
      python3-neutronclient \
    && apt-get clean \
    && apt-get purge -y --auto-remove \
    -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

# Workaround for Apache2+QEMU bug on Apple Silicon
RUN echo "Mutex posixsem" >> /etc/apache2/apache2.conf

ENV KOLLA_CONFIG_STRATEGY=COPY_ONCE
COPY config.json /var/lib/kolla/config_files/config.json
COPY src /var/lib/kolla/config_files/src

ENV MYSQL_ROOT_PASSWORD=root \
    KEYSTONE_ADMIN_PASSWORD=admin \
    KEYSTONE_DB_HOST=mariadb \
    KEYSTONE_DB_NAME=keystone \
    KEYSTONE_DB_PASSWORD=keystone \
    KEYSTONE_DB_USER=keystone \
    KEYSTONE_DEBUG="true"
