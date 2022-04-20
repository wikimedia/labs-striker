ARG KEYSTONE_IMAGE_TAG=train
FROM docker.io/kolla/ubuntu-binary-keystone:${KEYSTONE_IMAGE_TAG}

RUN set -eux; \
    apt-get clean && apt-get update \
    && DEBIAN_FRONTEND=noninteractive \
    apt-get install --yes --no-install-recommends \
      python3-mwclient \
    && apt-get clean \
    && apt-get purge -y --auto-remove \
    -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*

ENV KOLLA_CONFIG_STRATEGY=COPY_ONCE
COPY config.json /var/lib/kolla/config_files/config.json
COPY src /var/lib/kolla/config_files/src