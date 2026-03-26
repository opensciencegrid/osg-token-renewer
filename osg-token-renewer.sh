#!/bin/bash

CONFIG_PATH="${OSG_TOKEN_RENEWER_CONFIG_PATH:-/etc/osg/token-renewer/config.ini}"

if ! grep -q '^[[:space:]]*password_file[[:space:]]*=' "$CONFIG_PATH"; then
  # client credentials mode only
  exec "$(dirname "$0")"/osg-token-renewer
fi

eval $(oidc-agent) >/dev/null
"$(dirname "$0")"/osg-token-renewer
oidc-agent -k >/dev/null

# oidc-agent does not clean up its old socket files, apparently
if [[ $OIDC_SOCK = /tmp/oidc-*/oidc-agent.* ]]; then
  if [[ -e $OIDC_SOCK ]]; then
    rm -f "$OIDC_SOCK"
  fi
  if [[ -d ${OIDC_SOCK%/*} ]]; then
    rmdir "${OIDC_SOCK%/*}"
  fi
fi

