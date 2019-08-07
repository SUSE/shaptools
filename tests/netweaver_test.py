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
        self._netweaver = netweaver.NetweaverInstance('ha1', 1, 'pass')
        self.assertEqual('01', self._netweaver.inst)

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
        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass')
        self.assertEqual(proc_mock, result)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol_error(self, mock_execute):
        cmd = 'sapcontrol -nr 00 -function mycommand'
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        proc_mock.cmd = cmd

        mock_execute.return_value = proc_mock
        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver._execute_sapcontrol('mycommand')

        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass')
        self.assertTrue(
            'Error running sapcontrol command: {}'.format(cmd) in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_execute_sapcontrol_error_exception(self, mock_execute):
        cmd = 'sapcontrol -nr 00 -function mycommand'
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        proc_mock.cmd = cmd

        mock_execute.return_value = proc_mock
        result = self._netweaver._execute_sapcontrol('mycommand', False)

        mock_execute.assert_called_once_with(cmd, 'ha1adm', 'pass')
        self.assertEqual(proc_mock, result)

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
        mock_execute_cmd.assert_called_once_with(cmd, 'root', 'pass')

    @mock.patch('shaptools.shell.execute_cmd')
    def test_install_error(self, mock_execute_cmd):

        result = mock.Mock(returncode=1)
        mock_execute_cmd.return_value = result

        with self.assertRaises(netweaver.NetweaverError) as err:
            self._netweaver.install('/path', 'virtual', 'MYPRODUCT', '/inifile.params', 'root', 'pass')

        cmd = '/path/sapinst SAPINST_USE_HOSTNAME=virtual '\
            'SAPINST_EXECUTE_PRODUCT_ID=MYPRODUCT '\
            'SAPINST_SKIP_SUCCESSFULLY_FINISHED_DIALOG=true SAPINST_START_GUISERVER=false '\
            'SAPINST_INPUT_PARAMETERS_URL=/inifile.params'
        mock_execute_cmd.assert_called_once_with(cmd, 'root', 'pass')
        self.assertTrue('SAP Netweaver installation failed' in str(err.exception))

    @mock.patch('shaptools.shell.remove_user')
    def test_uninstall(self, mock_remove_user):

        self._netweaver.install = mock.Mock()
        self._netweaver.uninstall('/path', 'virtual', '/inifile.params', 'root', 'pass')

        self._netweaver.install.assert_called_once_with(
            '/path', 'virtual', 'NW_Uninstall:GENERIC.IND.PD', '/inifile.params', 'root', 'pass')
        mock_remove_user.assert_called_once_with('ha1adm', True, 'root', 'pass')

    def test_get_process_list(self):
        mock_result = mock.Mock(returncode=0)
        self._netweaver._execute_sapcontrol = mock.Mock(return_value=mock_result)
        result = self._netweaver.get_process_list()
        self._netweaver._execute_sapcontrol.assert_called_once_with(
            'GetProcessList', exception=False)
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
