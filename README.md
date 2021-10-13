The OSG Token Renewal Service
----------------------------- 

The OSG token renewal service is set up as a "oneshot" systemd service,
which runs under the `osg-token-svc` user, sets up an `oidc-agent`,
adds the relevant OIDC client accounts as specified in the `config.ini`
with `oidc-add`, and generates the tokens with `oidc-token`.

This service is set to run via a systemd timer approximately every 15 minutes.

If you would like to run the service manually at a different time (e.g., to generate
all the tokens immediately), you can run the service once with:

```console
root@host # systemctl start osg-token-renewer
```

If this succeeds, the new token will be written to the location you configured
for `token_path` (`/etc/osg/tokens/<ACCOUNT_SHORTNAME>.token`, by convention).

Failures can be diagnosed by running:

```console
root@host # journalctl -eu osg-token-renewer
```


Configuring the OSG Token Renewal Service
----------------------------------------- 

The main configuration file for the service is `/osg/token-renewer/config.ini`.

For each OIDC Client, you will add an `account` section to the config file.
For each token you wish to generate for this client account,
you will configure a `token` section with any relevant options.

Examples of this can be found in the `/osg/token-renewer/config.ini` that gets
installed with the package.

Each `[account <ACCOUNT_SHORTNAME>]` section corresponds to a client account
named `<ACCOUNT_SHORTNAME>`, set up with the `oidc-gen` tool, run by the
`osg-token-renewer-setup.sh` script.

In this `account` section, the `password_file` option is a path to a file
you create as `root` with the encryption password to be used for this client
account.

Details for this configuration can be found in the
[documentation here](https://opensciencegrid.org/docs/other/osg-token-renewer/#configuring-tokens).

For each client account, you can configure one or more `[token <TOKEN_NAME>]`
sections, where `<TOKEN_NAME>` is a unique name of your choosing.
These sections describe how to create the token with the `oidc-token` tool.
For details, see the 
[documentation here](https://opensciencegrid.org/docs/other/osg-token-renewer/#configuring-accounts).


