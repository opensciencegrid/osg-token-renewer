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


def emsg(msg):
    print(msg, file=sys.stderr)


def get_config_dict(config):
    cfgx = dict(account={}, token={})

    for sec in config.sections():
        ss = sec.split()
        if len(ss) != 2 or ss[0] not in cfgx:
            return emsg(f"Unrecognized section '{sec}'")
        type_, name = ss
        cfgx[type_][name] = config[sec]

    return cfgx


def validate_config_dict(cfgx):
    # the only mandatory attributes here are:
    #  - [token TOKEN].account exists, and references [account ACCOUNT]
    #  - [account ACCOUNT].password_file exists

    for token in cfgx["token"]:
        account = cfgx["token"][token].get("account")
        if not account:
            return emsg(f"token {token}: missing 'account' attribute")
        elif account not in cfgx["account"]:
            return emsg(f"token {token}: missing 'account {account}' section")
        elif not cfgx["account"][account].get("password_file"):
            return emsg(f"account {account}: missing 'password_file' attribute")
        elif not cfgx["token"][token].get("token_path")
            return emsg(f"token {token}: missing 'token_path' attribute")

    return True


def add_all_accounts(cfgx):
    accounts = cfgx["account"]
    added = set()

    for token in cfgx["token"]:
        acct = cfgx["token"][token].get("account")
        if acct in added:
            continue
        print("account %s" % acct)
        pwfile = accounts[acct]['password_file']
        add_account(acct, pwfile)
        added.add(acct)


def make_all_tokens(cfgx):
    tokens = cfgx["token"]
    errors = 0

    for t in tokens:
        print("token %s" % t)
        for k,v in tokens[t].items():
            print("{}: {}".format(k,v))
        print("---")
        try:
            mktoken(tokens[t])
        except subprocess.CalledProcessError as e:
            emsg(f"Failed to create token '{t}': {e}")
            errors += 1
        except subprocess.CalledProcessError as e:
            emsg(f"Failed to create token '{t}': {e}")
            errors += 1
        except IOError as e:
            emsg(f"Failed to write token '{t}': {e}")
            errors += 1

        print("===")

        return errors


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
        emsg(f"No token generated for account '{account[0]}'")


def add_account(acct, pwfile):
    pwcmd = "cat '%s'" % pwfile.replace("'", r"'\''")
    cmd = ["oidc-add", "--pw-cmd=%s" % pwcmd, acct]
    out = subprocess.check_output(cmd).strip().decode('utf-8')
    print("# oidc-add ... %s (%s)" % (acct, out))


# handy functions, for potential use later to set file ownership
#
#import pwd, grp
#
#def get_uid(name):
#    return pwd.getpwnam(name).pw_uid  # also, .pw_gid
#
#
#def get_gid(gname):
#    return grp.getgrnam(gname).gr_gid


def main():
    config = configparser.ConfigParser()
    config_path = os.environ.get("OSG_TOKEN_RENEWER_CONFIG_PATH", CONFIG_PATH)
    config.read(config_path)
    if 'OIDC_SOCK' not in os.environ:
        os.environ['OIDC_SOCK'] = OIDC_SOCK

    cfgx = get_config_dict(config)
    if not cfgx or not validate_config_dict(cfgx):
        sys.exit(1)

    errors = 0
    add_all_accounts(cfgx)
    errors += make_all_tokens(cfgx)

    return errors


if __name__ == '__main__':
    sys.exit(main() > 1)

