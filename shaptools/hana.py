"""
SAP HANA management module

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2018-11-15
"""
#TODO: Modify code to work when multiple HANA instances are installed
#TODO: Check backup already exist method
#TODO: Copy ssfs files method? Add hostname? Or do this using salt
#TODO: Split commands by version. Create backup for example

from __future__ import print_function

import logging
import enum
import fileinput
import re

from shaptools import shell

# python2 and python3 compatibility for string usage
try:
    basestring
except NameError:  # pragma: no cover
    basestring = str


class HanaError(Exception):
    """
    Error during HANA command execution
    """


class SrStates(enum.Enum):
    """
    System replication states
    """
    DISABLED = 0
    PRIMARY = 1
    SECONDARY = 2


class SrStatusReturnCode(enum.Enum):
    NONE = 10
    ERROR = 11
    UNKNOWN = 12
    INITIALIZING = 13
    SYNCING = 14
    ACTIVE = 15

    @classmethod
    def get(cls, ordinal, default):
        try:
            return cls(ordinal)
        except ValueError:
            return default


class HanaInstance:
    """
    SAP HANA instance implementation

    Args:
        sid (str): SAP HANA sid to enable
        inst (str): SAP HANA instance number
        password (str): HANA instance password
    """

    PATH = '/usr/sap/{sid}/HDB{inst}/'
    INSTALL_EXEC = '{software_path}/DATA_UNITS/HDB_LCM_LINUX_X86_64/hdblcm'
    # SID is usualy written uppercased, but the OS user is always created lower case.
    HANAUSER = '{sid}adm'.lower()
    SYNCMODES = ['sync', 'syncmem', 'async']

    def __init__(self, sid, inst, password):
        # Force instance nr always with 2 positions.
        inst = '{:0>2}'.format(inst)
        if not all(isinstance(i, basestring) for i in [sid, inst, password]):
            raise TypeError(
                'provided sid, inst and password parameters must be str type')

        self._logger = logging.getLogger('{}{}'.format(sid, inst))
        self.sid = sid
        self.inst = inst
        self._password = password

    def _run_hana_command(self, cmd, exception=True):
        """
        Run hana command

        Args:
            cmd (str): HANA command
            exception (boolean): Raise HanaError non-zero return code (default true)

        Returns:
            ProcessResult: ProcessResult instance storing subprocess returncode,
                stdout and stderr
        """
        #TODO: Add absolute paths to hana commands using sid and inst number
        user = self.HANAUSER.format(sid=self.sid)
        result = shell.execute_cmd(cmd, user, self._password)

        if exception and result.returncode != 0:
            raise HanaError('Error running hana command: {}'.format(result.cmd))

        return result

    def is_installed(self):
        """
        Check if SAP HANA is installed

        Returns:
            bool: True if installed, False otherwise
        """
        user = self.HANAUSER.format(sid=self.sid)
        try:
            result = shell.execute_cmd('HDB info', user, self._password)
            return not result.returncode
        except EnvironmentError as err: #FileNotFoundError is not compatible with python2
            self._logger.error(err)
            return False

    @classmethod
    def update_conf_file(cls, conf_file, **kwargs):
        """
        Update config file parameters

        Args:
            conf_file (str): Path to the configuration file
            kwargs (opt): Dictionary with the values to be updated.
                Use the exact name of the SAP configuration file for the key

        kwargs can be used in the next two modes:
            update_conf_file(conf_file, sid='PRD', hostname='hana01')
            update_conf_file(conf_file, **{'sid': 'PRD', 'hostname': 'hana01'})
        """
        for key, value in kwargs.items():
            pattern = '^{key}=.*'.format(key=key)
            new_value = '{key}={value}'.format(key=key, value=value)
            for line in fileinput.input(conf_file, inplace=1):
                line = re.sub(pattern, new_value, line)
                print(line, end='')
        return conf_file

    @classmethod
    def create_conf_file(
            cls, software_path, conf_file, root_user, root_password):
        """
        Create SAP HANA configuration file

        Args:
            software_path (str): Path where SAP HANA software is downloaded
            conf_file (str): Path where configuration file will be created
            root_user (str): Root user name
            root_password (str): Root user password
        """
        executable = cls.INSTALL_EXEC.format(software_path=software_path)
        cmd = '{executable} --action=install '\
            '--dump_configfile_template={conf_file}'.format(
                executable=executable, conf_file=conf_file)
        result = shell.execute_cmd(cmd, root_user, root_password)
        if result.returncode:
            raise HanaError('SAP HANA configuration file creation failed')
        return conf_file

    @classmethod
    def install(cls, software_path, conf_file, root_user, password):
        """
        Install SAP HANA platform providing a configuration file

        Args:
            software_path (str): Path where SAP HANA software is downloaded
            conf_file (str): Path to the configuration file
            root_user (str): Root user name
            password (str): Root user password
        """
        # TODO: mount partition if needed
        # TODO: do some integrity check stuff
        executable = cls.INSTALL_EXEC.format(software_path=software_path)
        cmd = '{executable} -b --configfile={conf_file}'.format(
            executable=executable, conf_file=conf_file)
        result = shell.execute_cmd(cmd, root_user, password)
        if result.returncode:
            raise HanaError('SAP HANA installation failed')

    def uninstall(self, root_user, password, installation_folder='/hana/shared'):
        """
        Uninstall SAP HANA platform
        """
        cmd = '{installation_folder}/{sid}/hdblcm/hdblcm '\
            '--uninstall -b'.format(
                installation_folder=installation_folder, sid=self.sid.upper())
        result = shell.execute_cmd(cmd, root_user, password)
        if result.returncode:
            raise HanaError('SAP HANA uninstallation failed')

    def is_running(self):
        """
        Check if SAP HANA daemon is running

        Returns:
            bool: True if running, False otherwise
        """
        cmd = 'pidof hdb.sap{sid}_HDB{inst}'.format(
            sid=self.sid.upper(), inst=self.inst)
        result = shell.execute_cmd(cmd)
        return not result.returncode

    # pylint:disable=W1401
    def get_version(self):
        """
        Get SAP HANA version
        """
        cmd = 'HDB version'
        result = self._run_hana_command(cmd)
        version_pattern = shell.find_pattern(
            r'\s+version:\s+(\d+.\d+.\d+).*', result.output)
        if version_pattern is None:
            raise HanaError('Version pattern not found in command output')
        return version_pattern.group(1)

    def start(self):
        """
        Start hana instance
        """
        cmd = 'HDB start'
        self._run_hana_command(cmd)

    def stop(self):
        """
        Stop hana instance
        """
        cmd = 'HDB stop'
        self._run_hana_command(cmd)

    def get_sr_state(self):
        """
        Get system replication state for the current node.

        Note:
        The command reads the state from the configuration files
        and so the reported state may not match the actual state.

        Returns:
            SrStates: System replication state
        """
        cmd = 'hdbnsutil -sr_state'
        result = self._run_hana_command(cmd)

        if shell.find_pattern('.*mode: primary.*', result.output) is not None:
            return SrStates.PRIMARY
        if shell.find_pattern('.*mode: ({})'.format('|'.join(self.SYNCMODES)),
                              result.output) is not None:
            return SrStates.SECONDARY
        return SrStates.DISABLED

    def get_sr_state_details(self):
        """
        Get system replication state details for the current node.
        See also get_sr_status which can provide additional details
        by parsing the output of the SAP python script
        systemReplicationStatus.py.

        Note:
        The command reads the state from the configuration files
        and so the reported state may not match the actual state.

        Returns:
            dict containing details about replication state.
        """
        cmd = 'hdbnsutil -sr_state'
        result = self._run_hana_command(cmd)
        state = {}
        for line in result.output.splitlines():
            if "Site Mappings:" in line or "Host Mappings:" in line:
                break
            data = re.match(r'^\s*([^:]+):\s+(.*)$', line.strip())
            if data is not None:
                state[data.group(1)] = data.group(2)
        return state

    def sr_enable_primary(self, name):
        """
        Enable SAP HANA system replication as primary node

        Args:
            name (str): Name to give to the node
        """
        cmd = 'hdbnsutil -sr_enable --name={}'.format(name)
        self._run_hana_command(cmd)

    def sr_disable_primary(self):
        """
        Disable SAP HANA system replication as primary node
        """
        cmd = 'hdbnsutil -sr_disable'
        self._run_hana_command(cmd)

    def sr_register_secondary(
            self, name, remote_host, remote_instance,
            replication_mode, operation_mode):
        """
        Register SAP HANA system replication as secondary node

        Args:
            name (str): Name to give to the node
            remote_host (str): Primary node hostname
            remote_instance (str): Primary node instance
            replication_mode (str): Replication mode
            operation_mode (str): Operation mode
        """
        remote_instance = '{:0>2}'.format(remote_instance)
        cmd = 'hdbnsutil -sr_register --name={} --remoteHost={} '\
              '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                  name, remote_host, remote_instance, replication_mode, operation_mode)
        self._run_hana_command(cmd)

    def sr_unregister_secondary(self, primary_name):
        """
        Unegister SAP HANA system replication from primary node

        Args:
            name (str): Name to give to the node
        """
        cmd = 'hdbnsutil -sr_unregister --name={}'.format(primary_name)
        self._run_hana_command(cmd)

    def sr_changemode_secondary(self, new_mode):
        """
        Change secondary mode replication mode

        Args:
            new_mode (str): New mode between sync|syncmem|async
        """
        cmd = 'hdbnsutil -sr_changemode --mode={}'.format(new_mode)
        self._run_hana_command(cmd)


    def check_user_key(self, key_name):
        """
        Check the use key existance

        Args:
            key (str): Key name

        Returns: True if it exists, False otherwise
        """
        cmd = 'hdbuserstore list {}'.format(key_name)
        try:
            self._run_hana_command(cmd)
            return True
        except HanaError:
            return False

    def create_user_key(
            self, key_name, environment, user_name, user_password, database=None):
        """
        Create or update user key entry for the database
        Args:
            key_name (str): Key name
            environment (str): Database location (host:port)
            user_name (srt): User name
            user_password (str): User password
            database (str, opt): Database name in MDC environment
        """
        database = '@{}'.format(database) if database else None
        cmd = 'hdbuserstore set {key} {env}{db} {user} {passwd}'.format(
            key=key_name, env=environment, db=database,
            user=user_name, passwd=user_password)
        self._run_hana_command(cmd)

    def _hdbsql_connect(self, **kwargs):
        """
        Create hdbsql connection string

        Args:
            key_name (str, optional): Keystore to connect to sap hana db
            user_name (str, optional): User to connect to sap hana db
            user_password (str, optiona): Password to connecto to sap hana db
        """
        if kwargs.get('key_name', None):
            cmd = 'hdbsql -U {}'.format(kwargs['key_name'])
        elif kwargs.get('user_name', None) and kwargs.get('user_password', None):
            cmd = 'hdbsql -u {} -p {}'.format(
                kwargs['user_name'], kwargs['user_password'])
        else:
            raise ValueError(
                'key_name or user_name/user_password parameters must be used')
        return cmd

    def create_backup(
            self, database, backup_name,
            key_name=None, user_name=None, user_password=None):
        """
        Create the primary node backup. key_name or user_name/user_password
        combination, one of them must be provided

        Args:
            database (str): Database name
            backup_name (str): Backup name
            key_name (str): Key name
            user_name (str): User
            user_password (str): User password
        """
        #TODO: Version check

        hdbsql_cmd = self._hdbsql_connect(
            key_name=key_name, user_name=user_name, user_password=user_password)

        cmd = '{} -d {} '\
              '\\"BACKUP DATA FOR FULL SYSTEM USING FILE (\'{}\')\\"'.format(
                  hdbsql_cmd, database, backup_name)
        self._run_hana_command(cmd)

    def sr_cleanup(self, force=False):
        """
        Clean system replication state

        Args:
            force (bool): Force cleanup
        """
        cmd = 'hdbnsutil -sr_cleanup{}'.format(' --force' if force else '')
        self._run_hana_command(cmd)

    def _parse_replication_output(self, output):
        """
        Utility function to parse output of
        systemReplicationStatus.py
        TODO: Parse table data
        TODO: Parse local state
        """
        return {}

    def get_sr_status(self):
        """
        Get system replication status (parsed output
        of systemReplicationStatus.py).
        """
        cmd = 'HDBSettings.sh systemReplicationStatus.py'
        result = self._run_hana_command(cmd, exception=False)
        status = self._parse_replication_output(result.output)
        # TODO: Handle HANA bug where non-working SR resulted in RC 15
        # (see SAPHana RA)
        status["status"] = SrStatusReturnCode.get(result.returncode, SrStatusReturnCode.UNKNOWN)
        return status

    def set_ini_parameter(
            self, database, file_name, layer,
            section_name, parameter_name, parameter_value,
            layer_name=None, reconfig=False,
            key_name=None, user_name=None, user_password=None):
        """
        set HANA configuration parameters in ini file

        sql syntax:
        ALTER SYSTEM ALTER CONFIGURATION (<filename>, <layer>[, <layer_name>])
        SET (<section_name>,<parameter_name>) = <parameter_value> WITH RECONFIGURE

        Args:
            database (str): Database name
            file_name (str): ini configuration file name
            layer (str): target layer for the configuration change 'SYSTEM', 'HOST' or 'DATABASE'
            layer_name (str, optional): target either a tenant name or a target host name
            section_name (str): section name of parameter in ini file
            parameter_name (str): name of the parameter to be modified
            parameter_value (str): the value of the parameter to be set
            key_name (str): Key name
            user_name (str): User
            user_password (str): User password
        """

        hdbsql_cmd = self._hdbsql_connect(
            key_name=key_name, user_name=user_name, user_password=user_password)

        if layer in ('HOST', 'DATABASE') and layer_name is not None:
            layer_name_str = ', \'{}\''.format(layer_name)
        else:
            layer_name_str = ''

        reconfig_option = ' WITH RECONFIGURE' if reconfig else ''

        cmd = '{hdbsql_cmd} -d {db} '\
              '\"ALTER SYSTEM ALTER CONFIGURATION (\'{file_name}\', \'{layer}\'{layer_name}) SET\
                  (\'{section_name}\',\'{parameter_name}\') = \
                      \'{parameter_value}\'{reconfig};\"'.format(
                          hdbsql_cmd=hdbsql_cmd, db=database, file_name=file_name, layer=layer,
                          section_name=section_name, parameter_name=parameter_name,
                          parameter_value=parameter_value, layer_name=layer_name_str,
                          reconfig=reconfig_option)

        # TODO: return the HANA SQL Statement error if sql fails
        self._run_hana_command(cmd)

    def unset_ini_parameter(
            self, database, file_name, layer,
            section_name, parameter_name, layer_name=None,
            key_name=None, user_name=None, user_password=None):
        """
        unset HANA configuration parameters in ini file

        sql syntax:
        ALTER SYSTEM ALTER CONFIGURATION (<filename>, <layer>[, <layer_name>])
        UNSET (<section_name>,<parameter_name>);

        Args:
            database (str): Database name
            file_name (str): ini configuration file name
            layer (str): target layer for the configuration change 'SYSTEM', 'HOST' or 'DATABASE'
            layer_name (str, optional): target either a tenant name or a target host name
            section_name (str): section name of parameter in ini file
            parameter_name (str): name of the parameter to be modified
            database (str): Database name
            key_name (str): Key name
            user_name (str): User
            user_password (str): User password
        """

        hdbsql_cmd = self._hdbsql_connect(
            key_name=key_name, user_name=user_name, user_password=user_password)

        if layer in ('HOST', 'DATABASE') and layer_name is not None:
            layer_name_str = ", \'" + layer_name + "\'"
        else:
            layer_name_str = ''

        cmd = '{hdbsql_cmd} -d {db} '\
              '\"ALTER SYSTEM ALTER CONFIGURATION (\'{file_name}\', \'{layer}\'{layer_name}) UNSET\
                  (\'{section_name}\',\'{parameter_name}\');\"'.format(
                      hdbsql_cmd=hdbsql_cmd, db=database, file_name=file_name, layer=layer,
                      section_name=section_name, parameter_name=parameter_name,
                      layer_name=layer_name_str)

        self._run_hana_command(cmd)

    def reduce_memory_resources(
            self, global_allocation_limit_value, preload_column_tables_value=False,
            key_name=None, user_name=None, user_password=None):
        """
        reduce memory resources needed by hana

        sql example:
        ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET
        ('memorymanager', 'global_allocation_limit') = 'size_in_mb' WITH RECONFIGURE;

        ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') SET
        ('system_replication', 'preload_column_tables') = 'false' WITH RECONFIGURE;

        Args:
            database (str): Database name
            key_name (str): Key name
            user_name (str): User
            user_password (str): User password
        """
        self.set_ini_parameter(database='SYSTEMDB', file_name='global.ini', layer='SYSTEM',\
        section_name='memorymanager', parameter_name='global_allocation_limit',\
        parameter_value=global_allocation_limit_value, reconfig=True,\
        key_name=key_name, user_name=user_name, user_password=user_password)

        self.set_ini_parameter(database='SYSTEMDB', file_name='global.ini', layer='SYSTEM',\
        section_name='system_replication', parameter_name='preload_column_tables',\
        parameter_value=preload_column_tables_value, reconfig=True,\
        key_name=key_name, user_name=user_name, user_password=user_password)

    def reset_memory_parameters(
            self, key_name=None, user_name=None, user_password=None):
        """
        reset HANA memory resources parameters to default values

        sql example:
        ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') UNSET
        ('memorymanager', 'global_allocation_limit')

        ALTER SYSTEM ALTER CONFIGURATION ('global.ini', 'SYSTEM') UNSET
        ('system_replication', 'preload_column_tables');

        Args:
            key_name (str): Key name
            user_name (str): User
            user_password (str): User password
        """
        self.unset_ini_parameter(database='SYSTEMDB', file_name='global.ini', layer='SYSTEM',\
        section_name='memorymanager', parameter_name='global_allocation_limit',\
        key_name=key_name, user_name=user_name, user_password=user_password)

        self.unset_ini_parameter(database='SYSTEMDB', file_name='global.ini', layer='SYSTEM',\
        section_name='system_replication', parameter_name='preload_column_tables',\
        key_name=key_name, user_name=user_name, user_password=user_password)
"""
# pylint:disable=C0103
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    hana = HanaInstance('prd', '00', 'Qwerty1234')
    if not hana.is_running():
        hana.start()
    state = hana.get_sr_state()
    if state == SrStates.PRIMARY:
        hana.sr_disable_primary()
    elif state == SrStates.SECONDARY:
        hana.stop()
        hana.sr_unregister_secondary('NUREMBERG')

    hana.create_backup('backupkey5', 'Qwerty1234', 'SYSTEMDB', 'backup')
    hana.sr_enable_primary('NUREMBERG')
    logging.getLogger(__name__).info(hana.get_sr_state())
"""
