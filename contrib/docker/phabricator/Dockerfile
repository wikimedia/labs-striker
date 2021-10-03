FROM docker.io/bitnami/phabricator:2021

# Add Wikimedia custom add-ons
USER root
RUN git clone https://github.com/wikimedia/phabricator-extensions /srv/phabricator-extensions
USER 1001
