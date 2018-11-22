"""
SAP HANA management module

:author: xarbulu
:organization: SUSE Linux GmbH
:contact: xarbulu@suse.com

:since: 2018-11-15
"""
#TODO: Check backup already exist method
#TODO: Copy ssfs files method? Add hostname? Or do this using salt
#TODO: Split commands by version. Create backup for example


import logging
import enum

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
        """
        if not self.is_installed():
            raise HanaError(
                'HANA is not installed properly sid {} and inst {} values'.format(
                    sid, inst))
        self._version = self.get_version()
        """

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

        if result.returncode:
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
        version_pattern = result.find_pattern('\s+version:\s+(\d+.\d+.\d+).*')
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
        Get system replication status in th current node

        Returns:
            SrStates: System replication state
        """
        cmd = 'hdbnsutil -sr_state'
        result = self._run_hana_command(cmd)

        if result.find_pattern('.*mode: primary.*'):
            return SrStates.PRIMARY
        if result.find_pattern('.*mode: ({})'.format('|'.join(self.SYNCMODES))):
            return SrStates.SECONDARY
        return SrStates.DISABLED

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
