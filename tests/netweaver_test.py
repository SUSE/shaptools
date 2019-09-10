"""
Unitary tests for netweaver.py.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-08-07
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

from shaptools import netweaver

class TestNetweaver(unittest.TestCase):
    """
    Unitary tests for netweaver.py.
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
        self._netweaver = netweaver.NetweaverInstance('ha1', '00', 'pass')

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
        self._netweaver = netweaver.NetweaverInstance('ha1', 1, 'pass', remote_host='remote')
        self.assertEqual('ha1', self._netweaver.sid)
        self.assertEqual('01', self._netweaver.inst)
        self.assertEqual('pass', self._netweaver._password)
        self.assertEqual('remote', self._netweaver.remote_host)

        with self.assertRaises(TypeError) as err:
            self._netweaver = netweaver.NetweaverInstance(1, '00', 'pass')

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

        with self.assertRaises(TypeError) as err:
            self._netweaver = netweaver.NetweaverInstance('ha1', '00', 1234)

        self.assertTrue(
            'provided sid, inst and password parameters must be str type' in
            str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0

        mock_execute.return_value = proc_mock

        result = self._netweaver._execute_sapcontrol('mycommand')

        cmd = 'sapcontrol -nr 00 -function mycommand'
        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass', None)
        self.assertEqual(proc_mock, result)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol_full(self, mock_execute):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0

        mock_execute.return_value = proc_mock

        result = self._netweaver._execute_sapcontrol(
            'mycommand', host='otherhost', user='newuser', password='newpass')

        cmd = 'sapcontrol -host otherhost -user newuser newpass -nr 00 -function mycommand'
        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass', None)
        self.assertEqual(proc_mock, result)


    def test_execute_sapcontrol_pass_missing(self):

        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver._execute_sapcontrol('mycommand', user='user')

        self.assertTrue('Password must be provided together with user')

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol_error(self, mock_execute):
        cmd = 'sapcontrol -nr 00 -function mycommand'
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        proc_mock.cmd = cmd

        mock_execute.return_value = proc_mock
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver._execute_sapcontrol('mycommand')

        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass', None)
        self.assertTrue(
            'Error running sapcontrol command: {}'.format(cmd) in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol_error_exception(self, mock_execute):
        cmd = 'sapcontrol -nr 00 -function mycommand'
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        proc_mock.cmd = cmd

        mock_execute.return_value = proc_mock
        result = self._netweaver._execute_sapcontrol('mycommand', exception=False)

        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass', None)
        self.assertEqual(proc_mock, result)

    @mock.patch('shaptools.shell.find_pattern')
    def test_get_attribute_from_file(self, mock_find_pattern):
        mock_find_pattern.return_value = 'found_attr'
        with mock.patch('shaptools.netweaver.open', mock.mock_open(read_data='filecontent')) as mock_open:
            attr = netweaver.NetweaverInstance.get_attribute_from_file('file', 'attr')
        mock_find_pattern.assert_called_once_with('attr', 'filecontent')
        self.assertEqual('found_attr', attr)

    @mock.patch('shaptools.shell.find_pattern')
    def test_is_ascs_installed(self, mock_find_pattern):

        mock_process = mock.Mock(output='output')
        mock_find_pattern.side_effect = ['found', 'found']

        self.assertTrue(self._netweaver._is_ascs_installed(mock_process))

        mock_find_pattern.assert_has_calls([
            mock.call(r'msg_server, MessageServer,.*', 'output'),
            mock.call(r'enserver, EnqueueServer,', 'output')
        ])

        mock_find_pattern.reset_mock()
        mock_find_pattern.side_effect = ['found', '']

        self.assertFalse(self._netweaver._is_ascs_installed(mock_process))

        mock_find_pattern.assert_has_calls([
            mock.call(r'msg_server, MessageServer,.*', 'output'),
            mock.call(r'enserver, EnqueueServer,', 'output')
        ])

    @mock.patch('shaptools.shell.find_pattern')
    def test_is_ers_installed(self, mock_find_pattern):

        mock_process = mock.Mock(output='output')
        mock_find_pattern.side_effect = ['found']

        self.assertTrue(self._netweaver._is_ers_installed(mock_process))

        mock_find_pattern.assert_called_once_with(
            r'enrepserver, EnqueueReplicator.*', 'output')

        mock_find_pattern.reset_mock()
        mock_find_pattern.side_effect = ['']

        self.assertFalse(self._netweaver._is_ers_installed(mock_process))

        mock_find_pattern.assert_called_once_with(
            r'enrepserver, EnqueueReplicator.*', 'output')

    def test_is_installed(self):

        processes_mock = mock.Mock(returncode=0)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self.assertTrue(self._netweaver.is_installed())
        self._netweaver.get_process_list.assert_called_once_with(False)

        processes_mock = mock.Mock(returncode=3)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self.assertTrue(self._netweaver.is_installed())
        self._netweaver.get_process_list.assert_called_once_with(False)

        processes_mock = mock.Mock(returncode=4)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self.assertTrue(self._netweaver.is_installed())
        self._netweaver.get_process_list.assert_called_once_with(False)

        processes_mock = mock.Mock(returncode=1)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self.assertFalse(self._netweaver.is_installed())
        self._netweaver.get_process_list.assert_called_once_with(False)

    def test_is_installed_error(self):

        processes_mock = mock.Mock(returncode=0)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)

        with self.assertRaises(ValueError) as err:
            self._netweaver.is_installed('other')
        self._netweaver.get_process_list.assert_called_once_with(False)
        self.assertTrue('provided sap instance type is not valid: other' in str(err.exception))

    def test_is_installed_ascs(self):

        processes_mock = mock.Mock(returncode=0)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self._netweaver._is_ascs_installed = mock.Mock(return_value=True)
        self.assertTrue(self._netweaver.is_installed('ascs'))
        self._netweaver.get_process_list.assert_called_once_with(False)
        self._netweaver._is_ascs_installed.assert_called_once_with(processes_mock)

    def test_is_installed_ers(self):

        processes_mock = mock.Mock(returncode=0)
        self._netweaver.get_process_list = mock.Mock(return_value=processes_mock)
        self._netweaver._is_ers_installed = mock.Mock(return_value=True)
        self.assertTrue(self._netweaver.is_installed('ers'))
        self._netweaver.get_process_list.assert_called_once_with(False)
        self._netweaver._is_ers_installed.assert_called_once_with(processes_mock)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_install(self, mock_execute_cmd):

        result = mock.Mock(returncode=0)
        mock_execute_cmd.return_value = result

        self._netweaver.install('/path', 'virtual', 'MYPRODUCT', '/inifile.params', 'root', 'pass')
        cmd = '/path/sapinst SAPINST_USE_HOSTNAME=virtual '\
            'SAPINST_EXECUTE_PRODUCT_ID=MYPRODUCT '\
            'SAPINST_SKIP_SUCCESSFULLY_FINISHED_DIALOG=true SAPINST_START_GUISERVER=false '\
            'SAPINST_INPUT_PARAMETERS_URL=/inifile.params'
        mock_execute_cmd.assert_called_once_with(cmd, 'root', 'pass', None)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_install_error(self, mock_execute_cmd):

        result = mock.Mock(returncode=1)
        mock_execute_cmd.return_value = result

        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.install(
                '/path', 'virtual', 'MYPRODUCT', '/inifile.params', 'root', 'pass',
                remote_host='remote')

        cmd = '/path/sapinst SAPINST_USE_HOSTNAME=virtual '\
            'SAPINST_EXECUTE_PRODUCT_ID=MYPRODUCT '\
            'SAPINST_SKIP_SUCCESSFULLY_FINISHED_DIALOG=true SAPINST_START_GUISERVER=false '\
            'SAPINST_INPUT_PARAMETERS_URL=/inifile.params'
        mock_execute_cmd.assert_called_once_with(cmd, 'root', 'pass', 'remote')
        self.assertTrue('SAP Netweaver installation failed' in str(err.exception))

    @mock.patch('shaptools.netweaver.shell.find_pattern')
    def test_ascs_restart_needed(self, mock_find_pattern):

        installation_result = mock.Mock()
        installation_result.returncode = netweaver.NetweaverInstance.UNSPECIFIED_ERROR
        installation_result.output = 'output'
        mock_find_pattern.return_value = True

        result = netweaver.NetweaverInstance._ascs_restart_needed(installation_result)
        self.assertTrue(result)

        mock_find_pattern.reset_mock()
        installation_result = mock.Mock()
        installation_result.returncode = netweaver.NetweaverInstance.UNSPECIFIED_ERROR
        installation_result.output = 'output'
        mock_find_pattern.return_value = False

        result = netweaver.NetweaverInstance._ascs_restart_needed(installation_result)
        self.assertFalse(result)

        installation_result = mock.Mock()
        installation_result.returncode = 0

        result = netweaver.NetweaverInstance._ascs_restart_needed(installation_result)
        self.assertFalse(result)

    @mock.patch('shaptools.netweaver.NetweaverInstance.get_attribute_from_file')
    @mock.patch('shaptools.netweaver.shell.find_pattern')
    def test_restart_ascs(self, mock_find_pattern, mock_get_attribute):
        mock_result1 = mock.Mock()
        mock_result1.group.return_value = 'HA1'

        mock_result2 = mock.Mock()
        mock_result2.group.return_value = '00'
        mock_get_attribute.side_effect = [mock_result1, mock_result2]

        mock_ascs_data = mock.Mock()
        mock_ascs_data.group.side_effect = ['ascs_hostname', 'ascs_inst']
        mock_find_pattern.return_value = mock_ascs_data

        # This patch.object tree is used to mock an instance of the class without mocking the class
        # methods
        with mock.patch.object(netweaver.NetweaverInstance, "__init__") as mock_instance:
            mock_instance.return_value = None
            with mock.patch.object(netweaver.NetweaverInstance, "get_system_instances") as mock_get_system_instances:
                mock_result = mock.Mock(output='output')
                mock_get_system_instances.return_value = mock_result
                with mock.patch.object(netweaver.NetweaverInstance, "stop") as mock_stop:
                    with mock.patch.object(netweaver.NetweaverInstance, "start") as mock_start:
                        netweaver.NetweaverInstance._restart_ascs('conf_file', 'ers_pass', 'ascs_pass')

        mock_get_attribute.assert_has_calls([
            mock.call('conf_file',  'NW_readProfileDir.profileDir += +.*/(.*)/profile'),
            mock.call('conf_file',  'nw_instance_ers.ersInstanceNumber += +(.*)')
        ])
        mock_result1.group.assert_called_once_with(1)
        mock_result2.group.assert_called_once_with(1)

        mock_instance.assert_called_once_with('ha1', '00', 'ers_pass', remote_host=None)

        mock_get_system_instances.assert_called_once_with(exception=False)

        mock_find_pattern.assert_called_once_with(
            '(.*), (.*), (.*), (.*), (.*), MESSAGESERVER|ENQUE, GREEN', 'output')

        mock_ascs_data.group.assert_has_calls([
            mock.call(1), mock.call(2)
        ])
        mock_stop.assert_called_once_with(
            host='ascs_hostname', inst='ascs_inst', user='ha1adm', password='ascs_pass')
        mock_start.assert_called_once_with(
            host='ascs_hostname', inst='ascs_inst', user='ha1adm', password='ascs_pass')

    @mock.patch('time.clock')
    @mock.patch('shaptools.netweaver.NetweaverInstance.get_attribute_from_file')
    @mock.patch('shaptools.netweaver.NetweaverInstance.install')
    @mock.patch('shaptools.netweaver.NetweaverInstance._ascs_restart_needed')
    @mock.patch('shaptools.netweaver.NetweaverInstance._restart_ascs')
    def test_install_ers_first_install(
            self, mock_restart, mock_restart_needed, mock_install,
            mock_get_attribute, mock_clock):

        mock_result = mock.Mock()
        mock_result.group.return_value = 'ers_pass'
        mock_get_attribute.return_value = mock_result

        mock_clock.return_value = 1
        mock_install_result = mock.Mock(returncode=111)
        mock_install.return_value = mock_install_result
        mock_restart_needed.return_value = True

        netweaver.NetweaverInstance.install_ers(
            'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
            ascs_password='ascs_pass', timeout=5, interval=1)

        mock_result.group.assert_called_once_with(1)
        mock_install.assert_called_once_with(
            'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
            exception=False, remote_host=None)
        mock_restart_needed.assert_called_once_with(mock_install_result)
        mock_restart.assert_called_once_with('conf_file', 'ers_pass', 'ascs_pass', None)

    @mock.patch('time.clock')
    @mock.patch('shaptools.netweaver.NetweaverInstance.get_attribute_from_file')
    @mock.patch('shaptools.netweaver.NetweaverInstance.install')
    @mock.patch('shaptools.netweaver.NetweaverInstance._ascs_restart_needed')
    @mock.patch('shaptools.netweaver.NetweaverInstance._restart_ascs')
    def test_install_ers_loop_install(
            self, mock_restart, mock_restart_needed, mock_install,
            mock_get_attribute, mock_sleep, mock_clock):

        mock_result = mock.Mock()
        mock_result.group.return_value = 'ers_pass'
        mock_get_attribute.return_value = mock_result

        mock_clock.side_effect = [1, 2, 3, 4, 5]
        mock_install_result = mock.Mock(returncode=111)
        mock_install.side_effect = [mock_install_result, mock_install_result, mock_install_result]
        mock_restart_needed.side_effect = [False, False, True]

        netweaver.NetweaverInstance.install_ers(
            'software', 'myhost', 'product', 'conf_file', 'user', 'pass', timeout=5, interval=1)

        mock_result.group.assert_called_once_with(1)

        mock_install.assert_has_calls([
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None)
        ])
        mock_restart_needed.assert_has_calls([
            mock.call(mock_install_result),
            mock.call(mock_install_result),
            mock.call(mock_install_result)
        ])
        mock_restart.assert_called_once_with('conf_file', 'ers_pass', 'ers_pass', None)
        mock_clock.assert_has_calls([
            mock.call(),
            mock.call(),
            mock.call()
        ])
        mock_sleep.assert_has_calls([
            mock.call(1),
            mock.call(1)
        ])

    @mock.patch('time.clock')
    @mock.patch('time.sleep')
    @mock.patch('shaptools.netweaver.NetweaverInstance.get_attribute_from_file')
    @mock.patch('shaptools.netweaver.NetweaverInstance.install')
    @mock.patch('shaptools.netweaver.NetweaverInstance._ascs_restart_needed')
    @mock.patch('shaptools.netweaver.NetweaverInstance._restart_ascs')
    def test_install_ers_loop_install(
            self, mock_restart, mock_restart_needed, mock_install,
            mock_get_attribute, mock_sleep, mock_clock):

        mock_result = mock.Mock()
        mock_result.group.return_value = 'ers_pass'
        mock_get_attribute.return_value = mock_result

        mock_clock.side_effect = [1, 2, 3, 4, 5]
        mock_install_result = mock.Mock(returncode=111)
        mock_install.side_effect = [mock_install_result, mock_install_result, mock_install_result]
        mock_restart_needed.side_effect = [False, False, True]

        netweaver.NetweaverInstance.install_ers(
            'software', 'myhost', 'product', 'conf_file', 'user', 'pass', timeout=5, interval=1)

        mock_result.group.assert_called_once_with(1)

        mock_install.assert_has_calls([
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None)
        ])
        mock_restart_needed.assert_has_calls([
            mock.call(mock_install_result),
            mock.call(mock_install_result),
            mock.call(mock_install_result)
        ])
        mock_restart.assert_called_once_with('conf_file', 'ers_pass', 'ers_pass', None)
        self.assertEqual(mock_clock.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([
            mock.call(1),
            mock.call(1)
        ])

    @mock.patch('time.clock')
    @mock.patch('time.sleep')
    @mock.patch('shaptools.netweaver.NetweaverInstance.get_attribute_from_file')
    @mock.patch('shaptools.netweaver.NetweaverInstance.install')
    @mock.patch('shaptools.netweaver.NetweaverInstance._ascs_restart_needed')
    def test_install_ers_error_install(
            self, mock_restart_needed, mock_install,
            mock_get_attribute, mock_sleep, mock_clock):

        mock_result = mock.Mock()
        mock_result.group.return_value = 'ers_pass'
        mock_get_attribute.return_value = mock_result

        mock_clock.side_effect = [1, 2, 3, 5]
        mock_install_result = mock.Mock(returncode=111)
        mock_install.side_effect = [mock_install_result, mock_install_result, mock_install_result]
        mock_restart_needed.side_effect = [False, False, False]

        with self.assertRaises(netweaver.NetweaverError) as err:
            netweaver.NetweaverInstance.install_ers(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass', timeout=3, interval=1)
        self.assertTrue('SAP Netweaver ERS installation failed after 3 seconds' in str(err.exception))

        mock_result.group.assert_called_once_with(1)

        mock_install.assert_has_calls([
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None),
            mock.call(
                'software', 'myhost', 'product', 'conf_file', 'user', 'pass',
                exception=False, remote_host=None)
        ])
        mock_restart_needed.assert_has_calls([
            mock.call(mock_install_result),
            mock.call(mock_install_result),
            mock.call(mock_install_result)
        ])
        self.assertEqual(mock_clock.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)
        mock_sleep.assert_has_calls([
            mock.call(1),
            mock.call(1),
            mock.call(1)
        ])

    @mock.patch('shaptools.shell.remove_user')
    def test_uninstall(self, mock_remove_user):
        self._netweaver.install = mock.Mock()
        self._netweaver.uninstall(
            '/path', 'virtual', '/inifile.params', 'root', 'pass', remote_host='remote')

        self._netweaver.install.assert_called_once_with(
            '/path', 'virtual', 'NW_Uninstall:GENERIC.IND.PD',
            '/inifile.params', 'root', 'pass', remote_host='remote')
        mock_remove_user.assert_called_once_with('ha1adm', True, 'root', 'pass', 'remote')

    def test_get_process_list(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_process_list(host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetProcessList', exception=False, host='host')
        self.assertEqual(mock_result, result)

        self._netweaver._execute_sapcontrol.mock_reset()
        mock_result = mock.Mock(returncode=3)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_process_list()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetProcessList', exception=False)
        self.assertEqual(mock_result, result)

        self._netweaver._execute_sapcontrol.mock_reset()
        mock_result = mock.Mock(returncode=4)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_process_list()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetProcessList', exception=False)
        self.assertEqual(mock_result, result)

    def test_get_process_list_error(self):
        mock_result = mock.Mock(returncode=1, cmd='updated command')
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.get_process_list()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetProcessList', exception=False)
        self.assertTrue('Error running sapcontrol command: updated command' in str(err.exception))

    def test_get_system_instances(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_system_instances(host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetSystemInstanceList', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_get_system_instances_error(self):
        mock_result = mock.Mock(returncode=1, cmd='updated command')
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.get_system_instances()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetSystemInstanceList', exception=False)
        self.assertTrue('Error running sapcontrol command: updated command' in str(err.exception))

    def test_get_instance_properties(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_instance_properties(host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetInstanceProperties', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_get_instance_properties_error(self):
        mock_result = mock.Mock(returncode=1, cmd='updated command')
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.get_instance_properties()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetInstanceProperties', exception=False)
        self.assertTrue('Error running sapcontrol command: updated command' in str(err.exception))

    def test_start(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.start(wait=0, host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'Start', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_start_wait(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.start(wait=5, host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'StartWait 5 0', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_start_error(self):
        mock_result = mock.Mock(returncode=1, cmd='updated command')
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.start(wait=5)
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'StartWait 5 0', exception=False)
        self.assertTrue('Error running sapcontrol command: updated command' in str(err.exception))

    def test_stop(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.stop(wait=0, host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'Stop', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_stop_wait(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.stop(wait=5, host='host')
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'StopWait 5 0', exception=False, host='host')
        self.assertEqual(mock_result, result)

    def test_stop_error(self):
        mock_result = mock.Mock(returncode=1, cmd='updated command')
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.stop(wait=5)
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'StopWait 5 0', exception=False)
        self.assertTrue('Error running sapcontrol command: updated command' in str(err.exception))
