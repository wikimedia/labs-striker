#!/usr/bin/env bash
# Run manage.py using the MediaWiki-Vagrant created virtualenv.
#
STRIKER_DIR=$(dirname $(dirname $(readlink -f $0)))
exec sudo /usr/bin/env ${STRIKER_DIR}/.venv/bin/python ${STRIKER_DIR}/manage.py "$@"
