# SHAPCLI

shapcli is an executable tool to use the api provided by shaptools. It wraps most of the commands and
exposes them as a command line tool.

In order to use the utility the `shaptools` library must be installed (either using `pip` or `rpm` package).

## Disclaimer

This tool will only work if `shaptools` is installed for `python 3` version.

## Motivation

The major motivation behind this tools is to provide an easy way to run all of the tools provided by
SAP regarding HANA. It wraps the next commands: `HDB`, `hdbnsutil`, `hdbuserstore`,
`HDBSettings.sh`, `hdbsql`.

Using this tool be avoid the need to change to SAP users every time we need to run any of these
commands. This is really helpful when we are running other commands in the same time (as `crmsh`
commands for example). Besides, having all of them gathered in the same place makes the usage
easier.

## How to use

`shapcli` can be used providing the SAP HANA database information through command line or using a
json configuration file (the options are mutually exclusive).
Here an example of how to create the configuration file: [config.json](shapcli.config.example)

Here some examples:

```
shapcli -s sid -i 00 -p HANAPASSWORD hana version
shapcli -c config.json hana version
```

Check how it works and help output running:

```
shapcli -h
```

The main options are: `hana` and `sr`;

* `hana`: Commands to manage SAP HANA database general functionalities.
* `sr`: Commands to manage SAP HANA system replication.

Using the `-h` flag in each option will output a new help output. For example:

```
shapcli hana -h
```

### Running commands in remote nodes

The commands can be executed in remote nodes too. For that the `-r` or `--remote` flag have to be
used (or adding the `remote` entry in the configuration file [the `-r` flag has priority over the configuration file entry]).

```
shapcli -c config.json -r remotehost hana version
```

If the ssh keys of the current node is not installed in the remote host, the password must be
provided after the command. To avoid this, the ssh key of the current node can be authorized in the
remote node. By default, the ssh public key must be added in: `/usr/sap/PRD/home/.ssh/authorized_keys`
(where `PRD` is the SAP HANA instanse sid in uppercase)
