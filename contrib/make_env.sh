#!/usr/bin/env bash
set -euo pipefail
cat > ${1:?Missing target file} << _EOF
LOCAL_UID=$(id -u)
LOCAL_GID=$(id -g)
_EOF
