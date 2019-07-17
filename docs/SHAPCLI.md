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

Check how it works and help output running:

```
shapcli -h
```

This is the output:

```
Configuration file or sid,instance and passwords parameters must be provided

usage: shapcli [-h] [--verbosity VERBOSITY] [--remotely REMOTELY] [-c CONFIG]
               [-s SID] [-i INSTANCE] [-p PASSWORD]
               {hana,sr} ...

optional arguments:
  -h, --help            show this help message and exit
  --verbosity VERBOSITY
                        Python logging level. Options: DEBUG, INFO, WARN,
                        ERROR (INFO by default)
  --remotely REMOTELY   Run the command in other machine using ssh
  -c CONFIG, --config CONFIG
                        JSON configuration file with SAP HANA instance data
                        (sid, instance and password)
  -s SID, --sid SID     SAP HANA sid
  -i INSTANCE, --instance INSTANCE
                        SAP HANA instance
  -p PASSWORD, --password PASSWORD
                        SAP HANA password

subcommands:
  valid subcommands

  {hana,sr}             additional help
    hana                Commands to interact with SAP HANA databse
    sr                  Commands to interact with SAP HANA system replication
```

Using the `-h` flag in each option will output a new help output. For example:

```
shapcli hana -h
```

This is the output:

```
usage: shapcli hana [-h]
                    {is_running,version,start,stop,info,kill,overview,landscape,uninstall,dummy,hdbsql,user,backup}
                    ...

optional arguments:
  -h, --help            show this help message and exit

hana:
  {is_running,version,start,stop,info,kill,overview,landscape,uninstall,dummy,hdbsql,user,backup}
                        Commands to interact with SAP HANA databse
    is_running          Check if SAP HANA database is running
    version             Show SAP HANA database version
    start               Start SAP HANA database
    stop                Stop SAP HANA database
    info                Show SAP HANA database information
    kill                Kill all SAP HANA database processes
    overview            Show SAP HANA database overview
    landscape           Show SAP HANA database landscape
    uninstall           Uninstall SAP HANA database instance
    dummy               Get data from DUMMY table
    hdbsql              Run a sql command with hdbsql
    user                Create a new user key
    backup              Create node backup
```

And here some examples:

```
shapcli -s sid -i 00 -p HANAPASSWORD hana version
shapcli -c config.json hana version
```
