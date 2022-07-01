# Dockerfile for *local development*.
# Generated by Blubber from .pipeline/blubber.yaml
FROM docker-registry.wikimedia.org/python3-buster:latest AS dockerize
USER 0
ENV HOME="/root"
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install -y "ca-certificates" "wget" && rm -rf /var/lib/apt/lists/*
ARG LIVES_AS="somebody"
ARG LIVES_UID=65533
ARG LIVES_GID=65533
RUN (getent group "$LIVES_GID" || groupadd -o -g "$LIVES_GID" -r "$LIVES_AS") && (getent passwd "$LIVES_UID" || useradd -l -o -m -d "/home/$LIVES_AS" -r -g "$LIVES_GID" -u "$LIVES_UID" "$LIVES_AS") && mkdir -p "/srv/dockerize/bin" && chown "$LIVES_UID":"$LIVES_GID" "/srv/dockerize/bin" && mkdir -p "/opt/lib" && chown "$LIVES_UID":"$LIVES_GID" "/opt/lib"
ARG RUNS_AS="runuser"
ARG RUNS_UID=900
ARG RUNS_GID=900
RUN (getent group "$RUNS_GID" || groupadd -o -g "$RUNS_GID" -r "$RUNS_AS") && (getent passwd "$RUNS_UID" || useradd -l -o -m -d "/home/$RUNS_AS" -r -g "$RUNS_GID" -u "$RUNS_UID" "$RUNS_AS")
USER $LIVES_UID
ENV HOME="/home/somebody"
WORKDIR "/srv/dockerize/bin"
ENV DJANGO_SETTINGS_MODULE="striker.settings" DOCKERIZE_VERSION="v0.6.1" PIP_DISABLE_PIP_VERSION_CHECK="on" PIP_NO_CACHE_DIR="off" PYTHONBUFFERED="1" PYTHONDONTWRITEBYTECODE="1"
RUN /bin/bash "-c" "wget --no-verbose https://github.com/jwilder/dockerize/releases/download/${DOCKERIZE_VERSION}/dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz && tar -C /srv/dockerize/bin -xzvf dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz && rm dockerize-linux-amd64-${DOCKERIZE_VERSION}.tar.gz"
USER $RUNS_UID
ENV HOME="/home/$RUNS_AS"

FROM docker-registry.wikimedia.org/python3-buster:latest AS local-python
USER 0
ENV HOME="/root"
ENV DEBIAN_FRONTEND="noninteractive"
RUN apt-get update && apt-get install -y "build-essential" "default-libmysqlclient-dev" "gettext" "git" "libldap2-dev" "libsasl2-dev" "python3-dev" "python3-pip" && rm -rf /var/lib/apt/lists/*
RUN python3 "-m" "pip" "install" "-U" "setuptools!=60.9.0" && python3 "-m" "pip" "install" "-U" "wheel" "tox" "pip"
ARG LIVES_AS="somebody"
ARG LIVES_UID=65533
ARG LIVES_GID=65533
RUN (getent group "$LIVES_GID" || groupadd -o -g "$LIVES_GID" -r "$LIVES_AS") && (getent passwd "$LIVES_UID" || useradd -l -o -m -d "/home/$LIVES_AS" -r -g "$LIVES_GID" -u "$LIVES_UID" "$LIVES_AS") && mkdir -p "/srv/app" && chown "$LIVES_UID":"$LIVES_GID" "/srv/app" && mkdir -p "/opt/lib" && chown "$LIVES_UID":"$LIVES_GID" "/opt/lib"
ARG RUNS_AS="runuser"
ARG RUNS_UID=900
ARG RUNS_GID=900
RUN (getent group "$RUNS_GID" || groupadd -o -g "$RUNS_GID" -r "$RUNS_AS") && (getent passwd "$RUNS_UID" || useradd -l -o -m -d "/home/$RUNS_AS" -r -g "$RUNS_GID" -u "$RUNS_UID" "$RUNS_AS")
USER $LIVES_UID
ENV HOME="/home/somebody"
WORKDIR "/srv/app"
ENV DJANGO_SETTINGS_MODULE="striker.settings" PIP_DISABLE_PIP_VERSION_CHECK="on" PIP_NO_CACHE_DIR="off" PYTHONBUFFERED="1" PYTHONDONTWRITEBYTECODE="1"
COPY --chown=$LIVES_UID:$LIVES_GID ["requirements.txt", "test-requirements.txt", "./"]
ENV PIP_FIND_LINKS="file:///opt/lib/python" PIP_WHEEL_DIR="/opt/lib/python"
RUN mkdir -p "/opt/lib/python"
RUN python3 "-m" "pip" "wheel" "-r" "requirements.txt" "-r" "test-requirements.txt" && python3 "-m" "pip" "install" "--target" "/opt/lib/python/site-packages" "-r" "requirements.txt" "-r" "test-requirements.txt"
ENV PATH="/opt/lib/python/site-packages/bin:${PATH}" PYTHONPATH="/opt/lib/python/site-packages"
COPY --chown=$LIVES_UID:$LIVES_GID [".", "."]
COPY --chown=$LIVES_UID:$LIVES_GID --from=dockerize ["/srv/dockerize", "/srv/dockerize"]
ENV PIP_NO_INDEX="1"

LABEL blubber.variant="local-python" blubber.version="0.9.0+6331215"
