FROM docker.io/mediawiki:1.41

# XXX: it would be cool if the upstram image provided a helper script for this
RUN set -eux; \
    savedAptMark="$(apt-mark showmanual)"; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      libldap-dev libzip-dev \
    ; \
    docker-php-ext-install -j "$(nproc)" \
      ldap zip \
    ; \
    apt-mark auto '.*' > /dev/null; \
    apt-mark manual $savedAptMark libldap-dev libzip-dev; \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
    rm -rf /var/lib/apt/lists/*

COPY ./install-composer.sh /usr/local/bin/install-composer
RUN set -eux; \
    install-composer \
    && mv composer.phar /usr/local/bin/composer \
    && rm /usr/local/bin/install-composer

ENV MW_BRANCH=REL1_41 \
    GIT_ROOT=https://gerrit.wikimedia.org/r/mediawiki \
    MW_INSTALL_DIR=/var/www/html \
    MW_EXT_DIR=/var/www/html/extensions \
    MW_EXTS="OAuth LdapAuthentication OpenStackManager"

RUN set -eux; \
    for EXT in $MW_EXTS; do \
      git clone --single-branch --depth 1 --branch $MW_BRANCH \
          $GIT_ROOT/extensions/$EXT $MW_EXT_DIR/$EXT \
          && rm -rf $MW_EXT_DIR/$EXT/.git \
          && ls -lh $MW_EXT_DIR/$EXT; \
    done; \
    ls -lh $MW_EXT_DIR

RUN set -eux; \
    mv $MW_INSTALL_DIR/composer.local.json-sample $MW_INSTALL_DIR/composer.local.json \
    && sh -c "cd $MW_INSTALL_DIR && COMPOSER_ALLOW_SUPERUSER=1 composer update --no-dev" \
    && ls -lh $MW_INSTALL_DIR/vendor

RUN ln -s /var/www/html /var/www/html/w
COPY apache2.conf /etc/apache2/sites-enabled/000-default.conf
