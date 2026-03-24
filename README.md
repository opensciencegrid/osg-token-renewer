The OSG Token Renewal Service
----------------------------- 

The OSG token renewal service is set up as a "oneshot" systemd service
which runs under the `osg-token-svc` user.

It has two basic modes of operation, depending on if the oauth client
needs to do OIDC authentication or is using the "client credentials"
grant type.

If it needs to do OIDC authentication, it sets up an `oidc-agent`,
adds the relevant OIDC client accounts as specified in the `config.ini`
with `oidc-add`, and generates the tokens with `oidc-token`.

Otherwise with the "client credentials" grant type it simply contacts
the token issuer and requests a new access token.

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

The main configuration file for the service is `/etc/osg/token-renewer/config.ini`.

For each client, you will add an `account` section to the config file
as instructed by the `osg-token-renewer-setup` script.
For each token you wish to generate for this client account,
you will configure a `token` section with any relevant options by hand.

Examples of this can be found in the `/etc/osg/token-renewer/config.ini`
that gets installed with the package.

Each `[account <ACCOUNT_SHORTNAME>]` section corresponds to a client account
named `<ACCOUNT_SHORTNAME>`, defined in the `osg-token-renewer-setup` script.

When using OIDC mode, the `account` section only contains a `password_file`
option which is a path to a file you create as `root` with the password
to be used to encrypt the information for that client account.

When using the client credentials mode, the `account` section contains a
`token_request_url`, `client_id`, and `client_secret`.

Details for this configuration can be found in the
[documentation here](https://osg-htc.org/docs/other/osg-token-renewer/#configuring-accounts).

For each client account, you can configure one or more `[token <TOKEN_NAME>]`
sections, where `<TOKEN_NAME>` is a unique name of your choosing.
These sections define the path to a file to store the token and optional
parameters to use when requesting it.
For details, see the 
[documentation here](https://osg-htc.org/docs/other/osg-token-renewer/#configuring-tokens).

