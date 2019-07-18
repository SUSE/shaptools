# SHAPCLI

shapcli is an executable tool to use the api provided by shaptools. It wraps most of the commands and
exposes them as a command line tool.

In order to use the utility the `shaptools` library must be installed (either using `pip` or `rpm` package).

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
