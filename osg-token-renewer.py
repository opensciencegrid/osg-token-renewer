#!/usr/bin/env python3

import configparser
import subprocess
import sys
import os

CONFIG_PATH = '/etc/osg/tokens/renewer.ini'
OIDC_SOCK   = '/var/run/osg-token-renewer/oidc-agent'

#As root, the user runs oidc-gen -w device ACCOUNT_SHORTNAME

# oidc-gen -w device ClientNameo
# - misc prompts, including password, which can be got with --pw-cmd=CMD

# oidc-token --aud="<SERVER AUDIENCE>" <CLIENT NAME>


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


def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if 'OIDC_SOCK' not in os.environ:
        os.environ['OIDC_SOCK'] = OIDC_SOCK
    make_all_tokens(config)


if __name__ == '__main__':
    main()

