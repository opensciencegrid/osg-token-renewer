#!/bin/bash
set -e

fail () { echo "$@" >&2; exit 1; }

usage () {
  echo "usage: $(basename "$0") CLIENT_NAME scopes..."
  echo
  echo "   eg: $(basename "$0") myclient123 wlcg offline_access"
  echo
  exit 1
}

[[ $1 = -* ]] && usage
[[ $2 ]] || usage

cleanup () {
  oidc-agent -k >/dev/null
  if [[ $OIDC_SOCK = /tmp/oidc-*/oidc-agent.* ]]; then
    [[ -e $OIDC_SOCK ]] && rm -f "$OIDC_SOCK"
    [[ -d ${OIDC_SOCK%/*} ]] && rmdir "${OIDC_SOCK%/*}"
  fi
}

issuer=https://wlcg.cloud.cnaf.infn.it/
client_name=$1
shift
scopes=$*
pwfile=/etc/osg/tokens/$client_name.pw

[[ -e $pwfile ]] || fail "please create /etc/osg/tokens/$client_name.pw with" \
                         "encryption password"

eval $(oidc-agent)
trap cleanup EXIT

( echo "$issuer"
  echo "$scopes"
) | oidc-gen -w device --pw-cmd="cat /dev/fd/9" "$client_name" 9<"$pwfile"

echo
echo
echo "Add the following section to /etc/osg/token-renewer/config.ini :"
echo
echo "[account $client_name]"
echo
echo "password_file = /etc/osg/tokens/$client_name.pw"
echo


