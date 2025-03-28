# Copyright (c) 2021 Wikimedia Foundation and contributors.
# All Rights Reserved.
#
# This file is part of Striker.
#
# Striker is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Striker is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Striker.  If not, see <http://www.gnu.org/licenses/>.

this := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
PROJECT_DIR := $(dir $(this))
PIPELINE_DIR := $(PROJECT_DIR)/.pipeline
DOCKERIZE := /srv/dockerize/bin/dockerize
# Prefer Compose v2, but allow override on hosts that only have v1
COMPOSE ?= docker compose
NPM ?= fresh-node -- npm

help:
	@echo "Make targets:"
	@echo "============="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
.PHONY: help

start: .env  ## Start the docker-compose stack
	DOCKER_DEFAULT_PLATFORM=linux/amd64 $(COMPOSE) up --build --detach
.PHONY: start

stop:  ## Stop the docker-compose stack
	$(COMPOSE) stop
.PHONY: stop

restart: stop start  ## Restart the docker-compose stack
.PHONY: restart

status:  ## Show status of the docker-compose stack
	$(COMPOSE) ps
.PHONY: status

tail:  ## Tail logs from the docker-compose stack
	$(COMPOSE) logs --tail=1000 -f
.PHONY: tail

migrate:  ## Run `manage.py migrate`
	$(COMPOSE) exec striker $(DOCKERIZE) \
		-wait tcp://mariadb:3306 \
		-wait tcp://keystone:5000 \
		-timeout 90s \
		poetry run python3 manage.py migrate
.PHONY: migrate

init_licenses:
	$(COMPOSE) exec striker $(DOCKERIZE) \
		-wait tcp://mariadb:3306 \
		-wait tcp://keystone:5000 \
		-timeout 90s \
		poetry run python3 manage.py loaddata software_license.json
.PHONY: init_licenses

init: start migrate init_licenses  ## Initialize docker-compose stack
	$(COMPOSE) restart striker
.PHONY: init

test:  ## Run test suite
	$(COMPOSE) exec striker /bin/bash -c "\
		set -eux; \
		export -n PYTHONPATH PIP_FIND_LINKS PIP_WHEEL_DIR PIP_NO_INDEX; \
		tox \
	"
.PHONY: test

shell:  ## Open a shell
	$(COMPOSE) exec \
		-e PIP_FIND_LINKS= \
		-e PIP_NO_INDEX= \
		-e PIP_WHEEL_DIR= \
		striker /bin/bash
.PHONY: shell

gitlab:  ## Open a shell in gitlab container
	$(COMPOSE) exec gitlab /bin/bash
.PHONY: gitlab

phabricator:  ## Open a shell in phabricator container
	$(COMPOSE) exec phabricator /bin/bash
.PHONY: phabricator

node_modules: ## Install Node dependencies
	$(NPM) ci
build: node_modules ## Build static assets
	$(NPM) run build
watch: node_modules
	$(NPM) run build -- --watch
.PHONY: build watch

.env:  ## Generate a .env file for local development
	./contrib/make_env.sh ./.env
