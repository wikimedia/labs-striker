FROM docker.io/mediawiki:1.37

# XXX: it would be cool if the upstram image provided a helper script for this
RUN set -eux; \
    savedAptMark="$(apt-mark showmanual)"; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      libldap-dev \
    ; \
    docker-php-ext-install -j "$(nproc)" \
      ldap \
    ; \
    apt-mark auto '.*' > /dev/null; \
    apt-mark manual $savedAptMark; \
    ldd "$(php -r 'echo ini_get("extension_dir");')"/*.so \
      | awk '/=>/ { print $3 }' \
      | sort -u \
      | xargs -r dpkg-query -S \
      | cut -d: -f1 \
      | sort -u \
      | xargs -rt apt-mark manual; \
    \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false; \
    rm -rf /var/lib/apt/lists/*

ENV MW_BRANCH=REL1_37 \
    VENDOR_BRANCH=REL1_37 \
    GIT_ROOT=https://gerrit.wikimedia.org/r/mediawiki \
    MW_VENDOR_DIR=/var/www/html/vendor \
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

# XXX: There must be a better way to install Composer dependencies for
# extensions than this...
RUN set -eux; \
    rm -rf $MW_VENDOR_DIR \
    && git clone --single-branch --depth 1 --branch $VENDOR_BRANCH \
        $GIT_ROOT/vendor $MW_VENDOR_DIR \
    && rm -rf $MW_VENDOR_DIR/.git \
    && ls -lh $MW_VENDOR_DIR

RUN ln -s /var/www/html /var/www/html/w
COPY apache2.conf /etc/apache2/sites-enabled/000-default.conf
