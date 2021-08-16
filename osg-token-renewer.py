#!/usr/bin/env python3

import configparser
import subprocess
import sys
import os

CONFIG_PATH = '/etc/osg/token-renewer/config.ini'
OIDC_SOCK   = '/var/run/osg-token-renewer/oidc-agent'

#As root, the user runs oidc-gen -w device ACCOUNT_SHORTNAME

# oidc-gen -w device ClientNameo
# - misc prompts, including password, which can be got with --pw-cmd=CMD

# oidc-token --aud="<SERVER AUDIENCE>" <CLIENT NAME>


def get_config_dict(config):
    cfgx = dict(account={}, token={})

    for sec in config.sections():
        ss = sec.split()
        if len(ss) != 2 or ss[0] not in cfgx:
            print("Unrecognized section '%s'" % sec, file=sys.stderr)
            return None
        type_, name = ss
        cfgx[name] = config[sec]

    return cfgd


def validate_config_dict(cfgx):
    # the only mandatory attributes here are:
    #  - [token TOKEN].account exists, and references [account ACCOUNT]
    #  - [account ACCOUNT].password_file exists

    for token in cfgx["token"]:
        account = cfgx["token"][token].get("account")
        if not account:
            print("token %s: missing 'account' attribute" % token,
                  file=sys.stderr)
            return False
        elif account not in cfgx["account"]:
            print("token %s: missing 'account %s' section" % (token, account),
                  file=sys.stderr)
            return False
        elif not cfgx["account"][account].get("password_file"):
            print("account %s: missing 'password_file' attribute" % account,
                  file=sys.stderr)
            return False

    return True


def add_all_accounts(config):
    accts = [ sec for sec in config.sections() if sec.startswith("account ") ]

    for acct in accts:
        print(acct)
        if 'password_file' not in config[acct]:
            print("missing 'password_file' attr; skipping %s" % acct)
            continue
        shortname = acct.split()[1]
        pwfile = config[acct]['password_file']
        add_account(shortname, pwfile)


def make_all_tokens(config):
    tokens = [ sec for sec in config.sections() if sec.startswith("token ") ]

    for t in tokens:
        print(t)
        for k,v in config[t].items():
            print("{}: {}".format(k,v))
        print("---")
        mktoken(config[t])
        print("===")


def option_if(name, val):
    return ['--{}={}'.format(name, val)] if val else []


def mktoken(cfg):
    #oidc-token --aud="<SERVER AUDIENCE>" <CLIENT NAME> > <TOKEN PATH>
    prog    = ['oidc-token']
    aud     = option_if('aud',   cfg.get("audience")    )
    scope   = option_if('scope', cfg.get("scope")       )
    time    = option_if('time',  cfg.get("min_lifetime"))
    account = [cfg.get("account")]
    cmdline = prog + aud + scope + time + account
    dest    = cfg.get("token_path")
    print(cmdline)
    token_blob = subprocess.check_output(cmdline)
    if token_blob:
        print("> %s" % dest)
        with open(dest, "wb") as w:
            w.write(token_blob)
    else:
        print("No token generated for account '%s'" % account[0],
              file=sys.stderr)


def add_account(acct, pwfile):
    pwcmd = "cat '%s'" % pwfile.replace("'", r"'\''")
    cmd = ["oidc-add", "--pw-cmd=%s" % pwcmd, acct]
    out = subprocess.check_output(cmd).strip().decode('utf-8')
    print("# oidc-add ... %s (%s)" % (acct, out))


def main():
    config = configparser.ConfigParser()
    config_path = os.environ.get("OSG_TOKEN_RENEWER_CONFIG_PATH", CONFIG_PATH)
    config.read(config_path)
    if 'OIDC_SOCK' not in os.environ:
        os.environ['OIDC_SOCK'] = OIDC_SOCK

    cfgx = get_config_dict(config)
    if not cfgx or not validate_config_dict(cfgx):
        sys.exit(1)

    add_all_accounts(config)
    make_all_tokens(config)


if __name__ == '__main__':
    main()

