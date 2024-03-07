# Copyright (c) 2022 Wikimedia Foundation and contributors.
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

IMAGE := docker-registry.wikimedia.org/wikimedia/labs-striker:latest

help:
	@echo "Striker demo/testing server management"
	@echo "Make targets:"
	@echo "============="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
.PHONY: help

start: ## Start the docker-compose stack
	sudo systemctl start striker.service
.PHONY: start

stop:  ## Stop the docker-compose stack
	sudo systemctl stop striker.service
.PHONY: stop

restart:  ## Restart the docker-compose stack
	sudo systemctl restart striker.service
.PHONY: restart

status:  ## Show status of the docker-compose stack
	sudo systemctl status striker.service --no-pager --full || /bin/true
	docker-compose -f cloud-vps.yaml ps
.PHONY: status

pull:  ## Pull the latest image doen from the docker repo
	sudo docker pull ${IMAGE}
.PHONY: pull

update: pull restart  ## Update and restart
.PHONY: update

tail:  ## Tail logs from the docker-compose stack
	docker-compose -f cloud-vps.yaml logs -f
.PHONY: tail

migrate:  ## Run `manage.py migrate`
	docker-compose -f cloud-vps.yaml exec striker \
		poetry run python3 manage.py migrate
.PHONY: migrate

init_licenses:
	docker-compose -f cloud-vps.yaml exec striker \
		poetry run python3 manage.py loaddata software_license.json
.PHONY: init_licenses

createinitialrevisions: ## Run `manage.py createinitialrevisions`
	docker-compose -f cloud-vps.yaml exec striker \
		poetry run python3 manage.py createinitialrevisions
.PHONY: createinitialrevisions

init: start migrate init_licenses createinitialrevisions  ## Initialize docker-compose stack
	docker-compose -f cloud-vps.yaml restart striker
.PHONY: init

install:  ## install systemd unit
	sudo ln -s $(shell pwd)/striker.service /etc/systemd/system/striker.service
	sudo systemctl daemon-reload
	sudo systemctl enable striker
	sudo service striker start
.PHONY: install
