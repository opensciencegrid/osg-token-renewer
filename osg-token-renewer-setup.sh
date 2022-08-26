#!/bin/bash
set -e

fail () { echo "$@" >&2; exit 1; }

usage () {
  if [[ $1 ]]; then
    echo "$*"
    echo
  fi
  echo "usage: $(basename "$0") [options] CLIENT_NAME"
  echo
  echo "   eg: $(basename "$0") myclient123"
  echo
  echo "Options:"
  echo "  --pw-file /path/to/pwfile    Specify a password file"
  echo "  --manual                     Manual client registration"
  exit 1
}

pwfile=
pwfd=
manual=
while [[ $1 = -* ]]; do
case $1 in
  --pw-file ) pwfile=$2; shift 2 ;;
  --pw-fd   ) pwfd=$2;   shift 2 ;;  # internal option only
  --manual  ) manual='--manual'; shift 1 ;;
   -*       ) usage ;;
esac
done

[[ $1 ]] || usage
[[ $2 ]] && usage

[[ $UID = 0 || $USER = osg-token-svc ]] || usage '*** Please run as root!'

client_name=$1
if [[ $pwfd ]]; then
  if [[ $pwfile ]]; then
    usage "*** The --pw-file and --pw-fd options are mutually exclusive."
  fi
  pwfile=/dev/fd/$pwfd  # for existence check, not for opening
  [[ -e /dev/fd/$pwfd ]] ||
  fail "password fd $pwfd does not appear to be open"
else
  [[ $pwfile ]] || pwfile=/etc/osg/tokens/$client_name.pw

  [[ -e $pwfile ]] ||
  fail "please create /etc/osg/tokens/$client_name.pw with encryption password"
fi

cleanup () {
  oidc-agent -k >/dev/null
  if [[ $OIDC_SOCK = /tmp/oidc-*/oidc-agent.* ]]; then
    [[ -e $OIDC_SOCK ]] && rm -f "$OIDC_SOCK"
    [[ -d ${OIDC_SOCK%/*} ]] && rmdir "${OIDC_SOCK%/*}"
  fi
}

# Note: cannot pass --pw-file option to the script run as the service account,
# as the service account may not have access to open the file by name for
# reading.  Instead, we open the file as root for the service account process
# to inherit the already-open file descriptor.
if [[ $UID = 0 ]]; then
  # open $pwfile as root, then re-run this script under service account
  { exec su osg-token-svc -s /bin/bash -c '"$@"' -- - \
    "$0" $manual --pw-fd 9 "$client_name"
  } 9<"$pwfile"
fi

eval $(oidc-agent)
trap cleanup EXIT

oidc-gen -w device $manual --pw-cmd="cat <&$pwfd" "$client_name"

echo
echo
echo "Add the following section to /etc/osg/token-renewer/config.ini :"
echo
echo "[account $client_name]"
echo
echo "password_file = /etc/osg/tokens/$client_name.pw"
echo


