#!/bin/bash

eval $(oidc-agent) >/dev/null
osg-token-renewer
kill "$OIDCD_PID"

# oidc-agent does not clean up its old socket files, apparently
if [[ $OIDC_SOCK = /tmp/oidc-*/oidc-agent.* ]]; then
  [[ -e $OIDC_SOCK ]] && rm -f "$OIDC_SOCK"
  [[ -d ${OIDC_SOCK%/*} ]] && rmdir "${OIDC_SOCK%/*}"
fi

