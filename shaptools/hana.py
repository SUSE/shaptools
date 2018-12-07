"""
SAP HANA management module

:author: xarbulu
:organization: SUSE Linux GmbH
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
    HANAUSER = '{sid}adm'
    SYNCMODES = ['sync', 'syncmem', 'async']

    def __init__(self, sid, inst, password):
        if not all(isinstance(i, str) for i in [sid, inst, password]):
            raise TypeError(
                'provided sid, inst and password parameters must be str type')

        self._logger = logging.getLogger('{}{}'.format(sid, inst))
        self.sid = sid
        self.inst = inst
        self._password = password

    def _run_hana_command(self, cmd):
        """
        Run hana command

        Args:
            cmd (str): HANA command

        Returns:
            ProcessResult: ProcessResult instance storing subprocess returncode,
                stdout and stderr
        """
        #TODO: Add absolute paths to hana commands using sid and inst number
        user = self.HANAUSER.format(sid=self.sid)
        result = shell.execute_cmd(cmd, user, self._password)

        if result.returncode != 0:
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
        version_pattern = result.find_pattern(r'\s+version:\s+(\d+.\d+.\d+).*')
        if not version_pattern:
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
        Get system replication state details for the current node.

        Note:
        The command reads the status from the configuration files
        and so the reported status may not match the actual status.

        Returns:
            SrStates: System replication state
        """
        state = self.get_sr_state_details()
        mode = state.get("mode", "unknown")
        if mode == "primary":
            return SrStates.PRIMARY
        if mode in self.SYNCMODES:
            return SrStates.SECONDARY
        return SrStates.DISABLED

    def get_sr_state_details(self):
        """
        Get system replication state details for the current node.

        Note:
        The command reads the status from the configuration files
        and so the reported status may not match the actual status.

        Returns:
            dict containing details about replication state.
        """
        cmd = 'hdbnsutil -sr_state'
        result = self._run_hana_command(cmd)
        state = {}
        for line in result.output.splitlines():
            if "Site Mappings:" in line or "Host Mappings:" in line:
                break
            m = re.match(r'^\s*([^:]+):\s+(.*)$', line.strip())
            if m is not None:
                state[m.group(1)] = m.group(2)
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


    def check_user_key(self, key):
        """
        Check the use key existance

        Args:
            key (str): Key name

        Returns: True if it exists, False otherwise
        """
        cmd = 'hdbuserstore list {}'.format(key)
        try:
            self._run_hana_command(cmd)
            return True
        except HanaError:
            return False

    def create_user_key(
            self, key, environment, user, user_password, database=None):
        """
        Create or update user key entry for the database
        Args:
            key (str): Key name
            environment (str): Database location (host:port)
            user (srt): User name
            user_password (str): User password
            database (str, opt): Database name in MDC environment
        """
        database = '@{}'.format(database) if database else None
        cmd = 'hdbuserstore set {key} {env}{db} {user} {passwd}'.format(
            key=key, env=environment, db=database,
            user=user, passwd=user_password)
        self._run_hana_command(cmd)

    def create_backup(
            self, user_key, user_password, database, backup_name):
        """
        Create the primary node backup

        Args:
            user_key (str): User key name
            user_password (str): User key password
            database (str): Database name
            back_name (str): Backup name
        """
        #TODO: Version check
        cmd = 'hdbsql -U {} -d {} -p {} '\
              '\\"BACKUP DATA FOR FULL SYSTEM USING FILE (\'{}\')\\"'.format(
                  user_key, database, user_password, backup_name)
        self._run_hana_command(cmd)

    def sr_cleanup(self, force=False):
        """
        Clean system replication state

        Args:
            force (bool): Force cleanup
        """
        cmd = 'hdbnsutil -sr_cleanup{}'.format(' --force' if force else '')
        self._run_hana_command(cmd)
