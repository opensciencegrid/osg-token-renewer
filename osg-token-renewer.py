#!/usr/bin/env python3

import configparser
import subprocess
import requests
import jwt
import time
import sys
import os

CONFIG_PATH = '/etc/osg/token-renewer/config.ini'
OIDC_SOCK   = '/var/run/osg-token-renewer/oidc-agent'

#As root, the user runs oidc-gen -w device ACCOUNT_SHORTNAME

# oidc-gen -w device ClientNameo
# - misc prompts, including password, which can be got with --pw-file=FILE

# oidc-token --aud="<SERVER AUDIENCE>" <CLIENT NAME>


def emsg(msg, **fmtkw):
    print(msg.format(**fmtkw), file=sys.stderr)


def get_config_dict(config):
    cfgx = dict(account={}, token={})

    for sec in config.sections():
        ss = sec.split()
        if len(ss) != 2 or ss[0] not in cfgx:
            return emsg(f"Unrecognized config section '{sec}'")
        type_, name = ss
        cfgx[type_][name] = config[sec]
        cfgx[type_][name]['name'] = name

    return cfgx


E_NO_TOK_ACCT_ATTR = (
    "Config section [token {token}]: missing 'account' attribute")
E_NO_TOK_ACCT_SEC  = (
    "Config for [token {token}]: missing [account {account}] section")
E_NO_TOK_PATH_ATTR = (
    "Config section [token {token}]: missing 'token_path' attribute")
E_NO_ACCT_PW_OR_TRU_ATTR  = (
    "Config section [account {account}]: missing both 'password_file' and 'token_request_url' attributes")
E_NO_ACCT_CI_ATTR  = (
    "Config section [account {account}]: missing 'client_id'")
E_NO_ACCT_CS_ATTR  = (
    "Config section [account {account}]: missing 'client_secret'")


def validate_config_dict(cfgx):
    # the only mandatory attributes here are:
    #  - [token TOKEN].account exists, and references [account ACCOUNT]
    #  - [token TOKEN].token_path exists
    #  - [account ACCOUNT].password_file or [account ACCOUNT].token_request_url 
    #    exists

    for token in cfgx["token"]:
        account = cfgx["token"][token].get("account")
        if not account:
            return emsg(E_NO_TOK_ACCT_ATTR, token=token)
        elif account not in cfgx["account"]:
            return emsg(E_NO_TOK_ACCT_SEC, token=token, account=account)
        elif not cfgx["token"][token].get("token_path"):
            return emsg(E_NO_TOK_PATH_ATTR, token=token)
        elif not cfgx["account"][account].get("password_file"):
            if cfgx["account"][account].get("token_request_url"):
                if not cfgx["account"][account].get("client_id"):
                    return emsg(E_NO_ACCT_CI_ATTR, account=account)
                elif not cfgx["account"][account].get("client_secret"):
                    return emsg(E_NO_ACCT_CS_ATTR, account=account)
            else:
                return emsg(E_NO_ACCT_PW_OR_TRU_ATTR, account=account)

    return True


def add_all_accounts(cfgx):
    accounts = cfgx["account"]
    added = set()
    errors = 0

    for token in cfgx["token"]:
        acct = cfgx["token"][token].get("account")
        if acct in added:
            continue
        print("account %s" % acct)
        if 'password_file' in accounts[acct]:
            pwfile = accounts[acct]['password_file']
            errors += add_account(acct, pwfile)
        added.add(acct)

    return errors


def make_all_tokens(cfgx):
    accounts = cfgx["account"]
    tokens = cfgx["token"]
    errors = 0

    for token in tokens:
        print("token %s" % token)
        account = accounts[cfgx["token"][token].get("account")]
        if 'password_file' in account:
            errors += mk_oidc_token(tokens[token])
        else:
            errors += request_token(account, tokens[token])

    return errors


def option_if(name, val):
    return ['--{}={}'.format(name, val)] if val else []


def write_token(cfg, token_blob):
    dest    = cfg.get("token_path")
    print("> %s" % dest)
    try:
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb+") as w:
            w.write(token_blob)
    except Exception as e:
        emsg(f"Failed to write token '{cfg['name']}': {e}")
        return 1
    return 0


def mk_oidc_token(cfg):
    #oidc-token --aud="<SERVER AUDIENCE>" <CLIENT NAME> > <TOKEN PATH>
    prog    = ['oidc-token']
    aud     = option_if('aud',   cfg.get("audience")    )
    scope   = option_if('scope', cfg.get("scope")       )
    if scope == []:
        # A blank scope tells oidc-token to request the default scopes of
        # the refresh token instead of re-requesting the original scopes.
        scope = ["--scope", " "]
    min_lifetime = option_if('time',  cfg.get("min_lifetime"))
    acct = cfg.get("account")
    cmdline = prog + aud + scope + min_lifetime + [acct]
    print(cmdline)
    t = cfg['name']
    try:
        token_blob = subprocess.check_output(cmdline)
    except Exception as e:
        emsg(f"Failed to get token '{t}': {e}")
        return 1
    if token_blob:
        return write_token(cfg, token_blob)
    else:
        emsg(f"No token '{t}' generated for account '{acct}'")
        return 1

    return 0


def request_token(account, cfg):
    t = cfg['name']
    min_lifetime_str = cfg.get("min_lifetime")
    if min_lifetime_str != None:
        if not min_lifetime_str.isdigit():
            emsg(f"min_lifetime for token '{t}' is not a non-negative integer")
            return 1
        min_lifetime = int(min_lifetime_str)
        dest = cfg.get("token_path")
        try:
            with open(dest, 'r', encoding='utf-8') as file:
                oldtok = file.read().strip()
            options = {
                "verify_signature": False,
                "verify_aud": False,
                "verify_exp": False
            }
            exp = jwt.decode(oldtok, options=options)['exp']
            remaining = exp - int(time.time())
            if remaining > min_lifetime:
                emsg(f"{str(remaining)} seconds remaining in '{t}', not renewing")
                return 0
        except FileNotFoundError:
            pass
        except Exception as e:
            emsg(f"Couldn't read old '{t}' token expiration time, continuing: {e}")

    data={"grant_type": "client_credentials"}
    aud = cfg.get("audience")
    if aud != None:
        data['audience'] = aud
    scope = cfg.get("scope")
    if scope != None:
        data['scope'] = scope

    try:
        response = requests.post(
            account['token_request_url'],
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            data=data,
            auth=(account['client_id'], account['client_secret']),
            timeout=10
        )
        response.raise_for_status()
        response_data = response.json()
    except Exception as e:
        emsg(f"Failure requesting token '{t}': {e}")
        return 1

    if 'access_token' not in response_data:
        emsg(f"No access_token returned in response for token '{t}'")
        return 1
    access_token = response_data['access_token'] + '\n'
    return write_token(cfg, access_token.encode("utf-8"))


def add_account(acct, pwfile):
    # --pw-store is needed for issuers like CILogon that make a new
    # refresh token every time an access token is requested.
    # --skip-check prevents attempting to get an access token from
    # the token issuer at load time.
    cmd = ["oidc-add", "--skip-check", "--pw-store", "--pw-file=%s" % pwfile, acct]
    try:
        out = subprocess.check_output(cmd).strip().decode('utf-8')
    except subprocess.CalledProcessError as e:
        emsg(f"Failed to create account '{acct}': {e}")
        return 1
    print("# oidc-add ... %s (%s)" % (acct, out))
    return 0


def main():
    config = configparser.ConfigParser()
    config_path = os.environ.get("OSG_TOKEN_RENEWER_CONFIG_PATH", CONFIG_PATH)
    config.read(config_path)
    if 'OIDC_SOCK' not in os.environ:
        os.environ['OIDC_SOCK'] = OIDC_SOCK

    cfgx = get_config_dict(config)
    if not cfgx or not validate_config_dict(cfgx):
        sys.exit(1)

    errors = add_all_accounts(cfgx)
    errors += make_all_tokens(cfgx)

    return errors


if __name__ == '__main__':
    sys.exit(int(main() > 0))

