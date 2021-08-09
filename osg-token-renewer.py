#!/usr/bin/env python3

import configparser
import subprocess

CONFIG_PATH = '/etc/osg/tokens/renewer.ini'

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
    print("> %s" % dest)
    with open(dest, "wb") as w:
        w.write(token_blob)


def main():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    make_all_tokens(config)


if __name__ == '__main__':
    main()

