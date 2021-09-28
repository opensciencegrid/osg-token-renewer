#!/bin/bash

eval $(oidc-agent) >/dev/null
osg-token-renewer
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

