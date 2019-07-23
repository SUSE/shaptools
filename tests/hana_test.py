"""
Unitary tests for hana.py.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2018-11-16
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import unittest
import filecmp
import shutil

try:
    from unittest import mock
except ImportError:
    import mock

from shaptools import hana, shell

class TestHana(unittest.TestCase):
    """
    Unitary tests for hana.py.
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)

    def setUp(self):
        """
        Test setUp.
        """
        self._hana = hana.HanaInstance('prd', '00', 'pass')

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """

    def test_init(self):
        self._hana = hana.HanaInstance('prd', 1, 'pass')
        self.assertEqual('01', self._hana.inst)

        with self.assertRaises(TypeError) as err:
            self._hana = hana.HanaInstance(1, '00', 'pass')

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

        with self.assertRaises(TypeError) as err:
            self._hana = hana.HanaInstance('prd', '00', 1234)

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

    @mock.patch('platform.machine')
    def test_get_platform(self, mock_machine):
        mock_machine.return_value = 'x86_64'
        machine = hana.HanaInstance.get_platform()
        self.assertEqual(machine, 'X86_64')
        mock_machine.assert_called_once_with()

        mock_machine.reset_mock()
        mock_machine.return_value = 'ppc64le'
        machine = hana.HanaInstance.get_platform()
        self.assertEqual(machine, 'PPC64LE')
        mock_machine.assert_called_once_with()

    @mock.patch('platform.machine')
    def test_get_platform_error(self, mock_machine):
        mock_machine.return_value = 'ppc64'
        with self.assertRaises(ValueError) as err:
            hana.HanaInstance.get_platform()
        self.assertTrue('not supported platform: {}'.format('ppc64') in str(err.exception))
        mock_machine.assert_called_once_with()

    @mock.patch('shaptools.shell.execute_cmd')
    def test_run_hana_command(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0

        mock_execute.return_value = proc_mock

        result = self._hana._run_hana_command('test command')

        mock_execute.assert_called_once_with('test command', 'prdadm', 'pass', None)
        self.assertEqual(proc_mock, result)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_run_hana_command_error(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        proc_mock.cmd = 'updated command'

        mock_execute.return_value = proc_mock
        with self.assertRaises(hana.HanaError) as err:
            self._hana._run_hana_command('test command')

        mock_execute.assert_called_once_with('test command', 'prdadm', 'pass', None)
        self.assertTrue(
            'Error running hana command: {}'.format(
                'updated command') in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_is_installed(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        mock_execute.return_value = proc_mock

        result = self._hana.is_installed()

        mock_execute.assert_called_once_with('HDB info', 'prdadm', 'pass', None)

        self.assertTrue(result)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_is_installed_error(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        mock_execute.return_value = proc_mock

        result = self._hana.is_installed()

        mock_execute.assert_called_once_with('HDB info', 'prdadm', 'pass', None)

        self.assertFalse(result)

    @mock.patch('shaptools.shell.execute_cmd')
    @mock.patch('logging.Logger.error')
    def test_is_installed_not_found(self, logger, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        error = EnvironmentError('test exception')
        mock_execute.side_effect = error

        result = self._hana.is_installed()

        mock_execute.assert_called_once_with('HDB info', 'prdadm', 'pass', None)

        self.assertFalse(result)
        logger.assert_called_once_with(error)

    def test_update_conf_file(self):
        pwd = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(pwd+'/support/original.conf', '/tmp/copy.conf')
        conf_file = hana.HanaInstance.update_conf_file(
            '/tmp/copy.conf', sid='PRD',
            password='Qwerty1234', system_user_password='Qwerty1234')
        self.assertTrue(filecmp.cmp(pwd+'/support/modified.conf', conf_file))

        shutil.copyfile(pwd+'/support/original.conf', '/tmp/copy.conf')
        conf_file = hana.HanaInstance.update_conf_file(
            '/tmp/copy.conf',
            **{'sid': 'PRD', 'password': 'Qwerty1234', 'system_user_password': 'Qwerty1234'})
        self.assertTrue(filecmp.cmp(pwd+'/support/modified.conf', conf_file))

    @mock.patch('shaptools.hana.HanaInstance.get_platform')
    @mock.patch('shaptools.shell.execute_cmd')
    def test_create_conf_file(self, mock_execute, mock_get_platform):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        mock_execute.return_value = proc_mock
        mock_get_platform.return_value = 'my_arch'

        conf_file = hana.HanaInstance.create_conf_file(
            'software_path', 'conf_file.conf', 'root', 'pass')

        mock_execute.assert_called_once_with(
            'software_path/DATA_UNITS/HDB_LCM_LINUX_my_arch/hdblcm '
            '--action=install --dump_configfile_template={conf_file}'.format(
                conf_file='conf_file.conf'), 'root', 'pass', None)
        mock_get_platform.assert_called_once_with()
        self.assertEqual('conf_file.conf', conf_file)

    @mock.patch('shaptools.hana.HanaInstance.get_platform')
    @mock.patch('shaptools.shell.execute_cmd')
    def test_create_conf_file_error(self, mock_execute, mock_get_platform):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        mock_execute.return_value = proc_mock
        mock_get_platform.return_value = 'my_arch'

        with self.assertRaises(hana.HanaError) as err:
            hana.HanaInstance.create_conf_file(
                'software_path', 'conf_file.conf', 'root', 'pass')

        mock_execute.assert_called_once_with(
            'software_path/DATA_UNITS/HDB_LCM_LINUX_my_arch/hdblcm '
            '--action=install --dump_configfile_template={conf_file}'.format(
                conf_file='conf_file.conf'), 'root', 'pass', None)

        mock_get_platform.assert_called_once_with()

        self.assertTrue(
            'SAP HANA configuration file creation failed' in str(err.exception))

    @mock.patch('shaptools.hana.HanaInstance.get_platform')
    @mock.patch('shaptools.shell.execute_cmd')
    def test_install(self, mock_execute, mock_get_platform):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        mock_execute.return_value = proc_mock
        mock_get_platform.return_value = 'my_arch'

        hana.HanaInstance.install(
            'software_path', 'conf_file.conf', 'root', 'pass')

        mock_execute.assert_called_once_with(
            'software_path/DATA_UNITS/HDB_LCM_LINUX_my_arch/hdblcm '
            '-b --configfile={conf_file}'.format(
                conf_file='conf_file.conf'), 'root', 'pass', None)
        mock_get_platform.assert_called_once_with()

    @mock.patch('shaptools.hana.HanaInstance.get_platform')
    @mock.patch('shaptools.shell.execute_cmd')
    def test_install_error(self, mock_execute, mock_get_platform):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        mock_execute.return_value = proc_mock
        mock_get_platform.return_value = 'my_arch'

        with self.assertRaises(hana.HanaError) as err:
            hana.HanaInstance.install(
                'software_path', 'conf_file.conf', 'root', 'pass')

        mock_execute.assert_called_once_with(
            'software_path/DATA_UNITS/HDB_LCM_LINUX_my_arch/hdblcm '
            '-b --configfile={conf_file}'.format(
                conf_file='conf_file.conf'), 'root', 'pass', None)
        mock_get_platform.assert_called_once_with()

        self.assertTrue(
            'SAP HANA installation failed' in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_uninstall(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        mock_execute.return_value = proc_mock

        self._hana.uninstall('root', 'pass')

        mock_execute.assert_called_once_with(
            '/hana/shared/PRD/hdblcm/hdblcm --uninstall -b', 'root', 'pass', None)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_uninstall_error(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        mock_execute.return_value = proc_mock

        with self.assertRaises(hana.HanaError) as err:
            self._hana.uninstall('root', 'pass', 'path')

        mock_execute.assert_called_once_with(
            'path/PRD/hdblcm/hdblcm --uninstall -b', 'root', 'pass', None)

        self.assertTrue(
            'SAP HANA uninstallation failed' in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_is_running(self, mock_execute):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_result = mock.Mock(returncode=0)
        self._hana._run_hana_command.return_value = mock_result
        result = self._hana.is_running()
        mock_command.assert_called_once_with('pidof hdb.sapPRD_HDB00', exception=False)
        self.assertTrue(result)

    @mock.patch('subprocess.Popen')
    def test_get_version(self, mock_popen):
        out = (b"Output text\n"
               b"  version:  1.2.3.4.5\n"
               b"line2")

        mock_popen_inst = mock.Mock()
        mock_popen_inst.returncode = 0
        mock_popen_inst.communicate.return_value = (out, b'err')
        mock_popen.return_value = mock_popen_inst

        version = self._hana.get_version()

        self.assertEqual('1.2.3', version)

    @mock.patch('subprocess.Popen')
    def test_get_version_error(self, mock_popen):
        out = (b"Output text\n"
               b"  versionn:  1.2.3.4.5\n"
               b"line2")

        mock_popen_inst = mock.Mock()
        mock_popen_inst.returncode = 0
        mock_popen_inst.communicate.return_value = (out, b'err')
        mock_popen.return_value = mock_popen_inst

        with self.assertRaises(hana.HanaError) as err:
            self._hana.get_version()

        self.assertTrue(
            'Version pattern not found in command output' in str(err.exception))

    def test_start(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.start()
        mock_command.assert_called_once_with('HDB start')

    def test_stop(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.stop()
        mock_command.assert_called_once_with('HDB stop')

    @mock.patch('shaptools.shell.find_pattern', mock.Mock(return_value=object()))
    def test_get_sr_state_primary(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        state = self._hana.get_sr_state()
        self.assertEqual('PRIMARY', state)
        mock_command.assert_called_once_with('hdbnsutil -sr_state')

    @mock.patch('shaptools.shell.find_pattern', mock.Mock(side_effect = [None, object()]))
    def test_get_sr_state_secondary(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        state = self._hana.get_sr_state()
        self.assertEqual('SECONDARY', state)
        mock_command.assert_called_once_with('hdbnsutil -sr_state')

    @mock.patch('shaptools.shell.find_pattern', mock.Mock(return_value=None))
    def test_get_sr_state_disabled(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        state = self._hana.get_sr_state()
        self.assertEqual('DISABLED', state)
        mock_command.assert_called_once_with('hdbnsutil -sr_state')

    def test_enable(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.sr_enable_primary('test')
        mock_command.assert_called_once_with(
            'hdbnsutil -sr_enable --name={}'.format('test'))

    def test_disable(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.sr_disable_primary()
        mock_command.assert_called_once_with('hdbnsutil -sr_disable')

    @mock.patch('shaptools.shell.create_ssh_askpass')
    def test_copy_ssfs_files(self, mock_sshpass):
        mock_sshpass.side_effect = ['cmd1', 'cmd2']
        self._hana._run_hana_command = mock.Mock()
        self._hana.copy_ssfs_files('host', 'prim_pass')
        mock_sshpass.assert_has_calls([
            mock.call(
                'prim_pass', "scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null "\
                '{user}@{remote_host}:/usr/sap/{sid}/SYS/global/security/rsecssfs/data/SSFS_{sid}.DAT '\
                '/usr/sap/{sid}/SYS/global/security/rsecssfs/data/SSFS_{sid}.DAT'.format(
                    user='prdadm', remote_host='host', sid='PRD')),
            mock.call(
                'prim_pass', 'scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null '\
                '{user}@{remote_host}:/usr/sap/{sid}/SYS/global/security/rsecssfs/key/SSFS_{sid}.KEY '\
                '/usr/sap/{sid}/SYS/global/security/rsecssfs/key/SSFS_{sid}.KEY'.format(
                    user='prdadm', remote_host='host', sid='PRD')),
        ])
        self._hana._run_hana_command.assert_has_calls([
            mock.call('cmd1'),
            mock.call('cmd2'),
        ])


    @mock.patch('time.clock')
    def test_register_basic(self, mock_clock):
        mock_clock.return_value = 0
        self._hana._run_hana_command = mock.Mock()
        result_mock = mock.Mock(returncode=0)
        self._hana._run_hana_command.return_value = result_mock
        self._hana.sr_register_secondary('test', 'host', 1, 'sync', 'ops')
        self._hana._run_hana_command.assert_called_once_with(
            'hdbnsutil -sr_register --name={} --remoteHost={} '\
            '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
            'test', 'host', '01', 'sync', 'ops'), False)

    @mock.patch('time.clock')
    def test_register_copy_ssfs(self, mock_clock):
        mock_clock.return_value = 0
        self._hana._run_hana_command = mock.Mock()
        result_mock = mock.Mock(returncode=149)
        self._hana.copy_ssfs_files = mock.Mock()
        self._hana._run_hana_command.return_value = result_mock
        self._hana.sr_register_secondary('test', 'host', 1, 'sync', 'ops', primary_pass='pass')
        self._hana._run_hana_command.assert_has_calls([
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False),
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'))
        ])
        self._hana.copy_ssfs_files.assert_called_once_with('host', 'pass')

    @mock.patch('time.clock')
    @mock.patch('time.sleep')
    def test_register_loop(self, mock_sleep, mock_clock):
        mock_clock.side_effect = [0, 1, 2, 3]
        self._hana._run_hana_command = mock.Mock()
        result_mock1 = mock.Mock(returncode=1)
        result_mock2 = mock.Mock(returncode=1)
        result_mock3 = mock.Mock(returncode=0)

        self._hana._run_hana_command.side_effect = [result_mock1, result_mock2, result_mock3]

        self._hana.sr_register_secondary('test', 'host', 1, 'sync', 'ops', timeout=5, interval=2)

        self._hana._run_hana_command.assert_has_calls([
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False),
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False),
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False)
        ])
        mock_sleep.assert_has_calls([mock.call(2), mock.call(2)])

    @mock.patch('time.clock')
    @mock.patch('time.sleep')
    def test_register_error(self, mock_sleep, mock_clock):
        mock_clock.side_effect = [0, 1, 2, 3]
        self._hana._run_hana_command = mock.Mock()
        result_mock1 = mock.Mock(returncode=1)
        result_mock2 = mock.Mock(returncode=1)
        result_mock3 = mock.Mock(returncode=1)

        self._hana._run_hana_command.side_effect = [result_mock1, result_mock2, result_mock3]

        with self.assertRaises(hana.HanaError) as err:
            self._hana.sr_register_secondary(
                'test', 'host', 1, 'sync', 'ops', timeout=2, interval=2)

        self.assertTrue(
            'System replication registration process failed after {} seconds'.format(2) in
            str(err.exception))

        self._hana._run_hana_command.assert_has_calls([
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False),
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False),
            mock.call(
                'hdbnsutil -sr_register --name={} --remoteHost={} '\
                '--remoteInstance={} --replicationMode={} --operationMode={}'.format(
                'test', 'host', '01', 'sync', 'ops'), False)
        ])
        mock_sleep.assert_has_calls([mock.call(2), mock.call(2), mock.call(2)])

    def test_unregister(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.sr_unregister_secondary('test')
        mock_command.assert_called_once_with(
            'hdbnsutil -sr_unregister --name={}'.format('test'))

    def test_changemode(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        self._hana.sr_changemode_secondary('sync')
        mock_command.assert_called_once_with(
            'hdbnsutil -sr_changemode --mode={}'.format('sync'))

    def test_check_user_key(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command

        result = self._hana.check_user_key('key')
        mock_command.assert_called_once_with(
            'hdbuserstore list {}'.format('key'))
        self.assertTrue(result)

    def test_check_user_key_error(self):
        mock_command = mock.Mock()
        mock_command.side_effect = hana.HanaError('test error')
        self._hana._run_hana_command = mock_command

        result = self._hana.check_user_key('key')
        mock_command.assert_called_once_with(
            'hdbuserstore list {}'.format('key'))
        self.assertFalse(result)

    def test_create_user_key(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command

        self._hana.create_user_key('key', 'envi', 'user', 'pass')
        mock_command.assert_called_once_with(
            'hdbuserstore set {key} {env}{db} {user} {passwd}'.format(
            key='key', env='envi', db=None,
            user='user', passwd='pass'))

    def test_create_user_key_db(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command

        self._hana.create_user_key('key', 'envi', 'user', 'pass', 'db')
        mock_command.assert_called_once_with(
            'hdbuserstore set {key} {env}{db} {user} {passwd}'.format(
            key='key', env='envi', db='@db',
            user='user', passwd='pass'))

    def test_hdbsql_connect_key(self):
        cmd = self._hana._hdbsql_connect(key_name='mykey')
        expected_cmd = 'hdbsql -i {} -U mykey'.format(self._hana.inst)
        self.assertEqual(expected_cmd, cmd)

    def test_hdbsql_connect_key_error(self):
        with self.assertRaises(ValueError) as err:
            self._hana._hdbsql_connect(key_name=None)
        self.assertTrue(
            'key_name or user_name/user_password parameters must be used' in str(
                err.exception))

    def test_hdbsql_connect_userpass(self):
        cmd = self._hana._hdbsql_connect(user_name='user', user_password='pass')
        expected_cmd = 'hdbsql -i {} -u user -p pass'.format(self._hana.inst)
        self.assertEqual(expected_cmd, cmd)

    def test_hdbsql_connect_userpass_error(self):
        with self.assertRaises(ValueError) as err:
            self._hana._hdbsql_connect(user_name=None, user_password=None)
        self.assertTrue(
            'key_name or user_name/user_password parameters must be used' in str(
                err.exception))

    def test_hdbsql_connect_error(self):
        with self.assertRaises(ValueError) as err:
            self._hana._hdbsql_connect()
        self.assertTrue(
            'key_name or user_name/user_password parameters must be used' in str(
                err.exception))

        with self.assertRaises(ValueError) as err:
            self._hana._hdbsql_connect(user_name='user')
        self.assertTrue(
            'key_name or user_name/user_password parameters must be used' in str(
                err.exception))

        with self.assertRaises(ValueError) as err:
            self._hana._hdbsql_connect(user_password='pass')
        self.assertTrue(
            'key_name or user_name/user_password parameters must be used' in str(
                err.exception))

    def test_create_backup(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.create_backup(
            'db', 'backup', 'key', 'key_user', 'key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{} -d {} '\
            '\\"BACKUP DATA FOR FULL SYSTEM USING FILE (\'{}\')\\"'.format(
            'hdbsql', 'db', 'backup'))

    def test_sr_cleanup(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command

        self._hana.sr_cleanup()
        mock_command.assert_called_once_with('hdbnsutil -sr_cleanup')

    def test_sr_cleanup_force(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command

        self._hana.sr_cleanup(force=True)
        mock_command.assert_called_once_with('hdbnsutil -sr_cleanup --force')

    def test_get_sr_state_details(self):
        expected_results = {
            "Not set (HDB daemon stopped)": { "online": "false", "mode": "none" },
            "Not set (HDB daemon running)": { "online": "true", "mode": "none" },
            "Primary (no secondary sync)": {'online': 'true', 'mode': 'primary', 'operation mode': 'primary', 'site id': '1', 'site name': 'NUREMBERG', 'is source system': 'true', 'is secondary/consumer system': 'false', 'has secondaries/consumers attached': 'false', 'is a takeover active': 'false'},
            "Primary (sync)": {'online': 'true', 'mode': 'primary', 'operation mode': 'primary', 'site id': '1', 'site name': 'NUREMBERG', 'is source system': 'true', 'is secondary/consumer system': 'false', 'has secondaries/consumers attached': 'true', 'is a takeover active': 'false'},
            "Secondary (sync)": {'online': 'true', 'mode': 'sync', 'operation mode': 'logreplay', 'site id': '2', 'site name': 'PRAGUE', 'is source system': 'false', 'is secondary/consumer system': 'true', 'has secondaries/consumers attached': 'false', 'is a takeover active': 'false', 'active primary site': '1', 'primary masters': 'hana01'},
            "Primary (kb7023127)": {'online': 'true', 'mode': 'primary', 'site id': '1', 'site name': 'node1'},
            "Secondary (kb7023127)": {'online': 'true', 'mode': 'sync', 'site id': '2', 'site name': 'node2', 'active primary site': '1'},
            }
        for desc, case in _hdbnsutil_sr_state_outputs.items():
            result = shell.ProcessResult("", 0, case.encode('utf-8'), "".encode('utf-8'))
            mock_command = mock.Mock()
            mock_command.return_value = result
            self._hana._run_hana_command = mock_command

            state = self._hana.get_sr_state_details()
            mock_command.assert_called_once_with('hdbnsutil -sr_state')

            self.assertEqual(state, expected_results.get(desc, {}))

    def test_get_sr_status(self):
        class Ret(object):
            def __init__(self, rc):
                self.returncode, self.output = rc, ""
        for rc, expect in ((13, 'INITIALIZING'), (4, 'UNKNOWN'), (15, 'ACTIVE')):
            self._hana._run_hana_command = mock.Mock(return_value=Ret(rc))
            status = self._hana.get_sr_status()
            self._hana._run_hana_command.assert_called_once_with(
                'HDBSettings.sh systemReplicationStatus.py', exception=False)
            self.assertEqual(status, {"status": expect})

    def test_set_ini_parameter(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.set_ini_parameter(
            ini_parameter_values=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit', 'parameter_value':'25000'}],
            database='db', file_name='global.ini', layer='SYSTEM',
            key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\') SET'
            '{ini_parameter_values};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini', layer='SYSTEM',
            ini_parameter_values='(\'memorymanager\',\'global_allocation_limit\')=\'25000\''))

    def test_set_ini_parameter_layer(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.set_ini_parameter(
            ini_parameter_values=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit', 'parameter_value':'25000'}],
            database='db', file_name='global.ini',
            layer='HOST', layer_name='host01',
            key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\', \'{layer_name}\') '
            'SET{ini_parameter_values};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini',
            layer='HOST', layer_name='host01',
            ini_parameter_values='(\'memorymanager\',\'global_allocation_limit\')=\'25000\''))

    def test_set_ini_parameter_reconfig(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.set_ini_parameter(
            ini_parameter_values=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit', 'parameter_value':'25000'}],
            database='db', file_name='global.ini', layer='SYSTEM',
            reconfig=True, key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\') SET'
            '{ini_parameter_values}{reconfig};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini', layer='SYSTEM',
            ini_parameter_values='(\'memorymanager\',\'global_allocation_limit\')=\'25000\'',
            reconfig=' WITH RECONFIGURE'))

    def test_unset_ini_parameter(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.unset_ini_parameter(
            ini_parameter_names=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit'}],
            database='db', file_name='global.ini', layer='SYSTEM',
            key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\') UNSET'
            '{ini_parameter_names};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini', layer='SYSTEM',
            ini_parameter_names='(\'memorymanager\',\'global_allocation_limit\')'))

    def test_unset_ini_parameter_layer(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.unset_ini_parameter(
            ini_parameter_names=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit'}],
            database='db', file_name='global.ini', layer='HOST', layer_name='host01',
            key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\', \'{layer_name}\') UNSET'
            '{ini_parameter_names};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini', layer='HOST', layer_name='host01',
            ini_parameter_names='(\'memorymanager\',\'global_allocation_limit\')'))

    def test_unset_ini_parameter_reconfig(self):
        mock_command = mock.Mock()
        self._hana._run_hana_command = mock_command
        mock_hdbsql = mock.Mock(return_value='hdbsql')
        self._hana._hdbsql_connect = mock_hdbsql

        self._hana.unset_ini_parameter(
            ini_parameter_names=[{'section_name':'memorymanager',
            'parameter_name':'global_allocation_limit'}],
            database='db', file_name='global.ini', layer='SYSTEM', reconfig=True,
            key_name='key', user_name='key_user', user_password='key_password')
        mock_hdbsql.assert_called_once_with(
            key_name='key', user_name='key_user', user_password='key_password')
        mock_command.assert_called_once_with(
            '{hdbsql} -d {db} '\
            '\\"ALTER SYSTEM ALTER CONFIGURATION(\'{file_name}\', \'{layer}\') UNSET'
            '{ini_parameter_names}{reconfig};\\"'.format(
            hdbsql='hdbsql', db='db', file_name='global.ini', layer='SYSTEM',
            ini_parameter_names='(\'memorymanager\',\'global_allocation_limit\')',
            reconfig=' WITH RECONFIGURE'))

_hdbnsutil_sr_state_outputs = {
    "Not set (HDB daemon stopped)": """nameserver hana01:30001 not responding.

System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~

online: false

mode: none
done.
""",
    "Not set (HDB daemon running)": """
System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~

online: true

mode: none
done.
""",
    "Primary (no secondary sync)": """

System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~

online: true

mode: primary
operation mode: primary
site id: 1
site name: NUREMBERG


is source system: true
is secondary/consumer system: false
has secondaries/consumers attached: false
is a takeover active: false

Host Mappings:
~~~~~~~~~~~~~~


Site Mappings:
~~~~~~~~~~~~~~
NUREMBERG (primary/)

Tier of NUREMBERG: 1

Replication mode of NUREMBERG: primary

Operation mode of NUREMBERG:

done.


""", "Primary (sync)": """
System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~

online: true

mode: primary
operation mode: primary
site id: 1
site name: NUREMBERG


is source system: true
is secondary/consumer system: false
has secondaries/consumers attached: true
is a takeover active: false

Host Mappings:
~~~~~~~~~~~~~~

hana01 -> [PRAGUE] hana02
hana01 -> [NUREMBERG] hana01


Site Mappings:
~~~~~~~~~~~~~~
NUREMBERG (primary/primary)
    |---PRAGUE (sync/logreplay)

Tier of NUREMBERG: 1
Tier of PRAGUE: 2

Replication mode of NUREMBERG: primary
Replication mode of PRAGUE: sync

Operation mode of NUREMBERG: primary
Operation mode of PRAGUE: logreplay

Mapping: NUREMBERG -> PRAGUE
done.
""",
    "Secondary (sync)": """
System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~

online: true

mode: sync
operation mode: logreplay
site id: 2
site name: PRAGUE


is source system: false
is secondary/consumer system: true
has secondaries/consumers attached: false
is a takeover active: false
active primary site: 1

primary masters: hana01

Host Mappings:
~~~~~~~~~~~~~~

hana02 -> [PRAGUE] hana02
hana02 -> [NUREMBERG] hana01


Site Mappings:
~~~~~~~~~~~~~~
NUREMBERG (primary/primary)
    |---PRAGUE (sync/logreplay)

Tier of NUREMBERG: 1
Tier of PRAGUE: 2

Replication mode of NUREMBERG: primary
Replication mode of PRAGUE: sync

Operation mode of NUREMBERG: primary
Operation mode of PRAGUE: logreplay

Mapping: NUREMBERG -> PRAGUE
done.
    """,
    "Primary (kb7023127)": """checking for active or inactive nameserver ...

System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~
online: true

mode: primary
site id: 1
site name: node1

Host Mappings:
~~~~~~~~~~~~~~

sapn1 -> [node1] sapn1
sapn1 -> [node2] sapn2


done.
    """,
    "Secondary (kb7023127)": """checking for active or inactive nameserver ...

System Replication State
~~~~~~~~~~~~~~~~~~~~~~~~
online: true

mode: sync
site id: 2
site name: node2
active primary site: 1


Host Mappings:
~~~~~~~~~~~~~~

sapn2 -> [node1] sapn1
sapn2 -> [node2] sapn2

primary masters:sapn1

done.
"""
    }
