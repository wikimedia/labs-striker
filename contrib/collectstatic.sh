#!/usr/bin/env bash
# Ugly collectstatic command to keep django-autocomplete-light from making
# a mess of the staticfiles directory.
#
# This is meant to be run as a post-install script on production targets.
#
# Django's collect static maintenance script has an --ignore option, but
# strangely the way that it is implemented inside the script you can only
# exclude based on the name of a single directory or file. Ideally you would be
# able to exclude a more descriptive path such as
# django-autocomplete-light/vendor/vendor
#
set -e
set -x
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

STRIKER_DIR=$(dirname $(dirname $(readlink -f $0)))
exec /usr/bin/env ${VENV}/bin/python ${STRIKER_DIR}/manage.py collectstatic -c --noinput \
    --ignore src \
    --ignore tests \
    --ignore *.json \
    --ignore Gruntfile.js
cd $DIR/../staticfiles
python -mjson.tool staticfiles.json > staticfiles.json.pretty
mv staticfiles.json.pretty staticfiles.json
