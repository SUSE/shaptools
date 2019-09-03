"""
Unitary tests for shell.py.

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
import subprocess

try:
    from unittest import mock
except ImportError:
    import mock

from shaptools import shell

class TestShell(unittest.TestCase):
    """
    Unitary tests for shell.py.
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

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """

    @mock.patch('logging.Logger.info')
    @mock.patch('logging.Logger.error')
    def test_log_results(self, logger_error, logger_info):
        out = ("Output text\n"
               "line1\n"
               "line2")
        err = ("Error text\n"
               "err1\n"
               "err2")

        shell.log_command_results(out, err)

        logger_info.assert_has_calls([
            mock.call('Output text'),
            mock.call('line1'),
            mock.call('line2')
        ])

        logger_error.assert_has_calls([
            mock.call('Error text'),
            mock.call('err1'),
            mock.call('err2')
        ])

    @mock.patch('logging.Logger.info')
    @mock.patch('logging.Logger.error')
    def test_show_output_empty(self, logger_error, logger_info):
        shell.log_command_results("", "")
        self.assertEqual(0, logger_info.call_count)
        self.assertEqual(0, logger_error.call_count)

    def test_find_pattern(self):
        out = ("Output text\n"
               "  line1  \n"
               "line2")
        result = shell.find_pattern('.*line1.*', out)
        self.assertIsNotNone(result)

    def test_find_pattern_fail(self):
        out = ("Output text\n"
               "  line1  \n"
               "line2")
        result = shell.find_pattern('.*line3.*', out)
        self.assertIsNone(result)

    def test_format_su_cmd(self):
        cmd = shell.format_su_cmd('ls -la', 'test')
        self.assertEqual('su -lc "ls -la" test', cmd)

        cmd = shell.format_su_cmd('hdbnsutil -sr_enable --name=PRAGUE', 'prdadm')
        self.assertEqual('su -lc "hdbnsutil -sr_enable --name=PRAGUE" prdadm', cmd)

    def test_format_remote_cmd(self):
        cmd = shell.format_remote_cmd('ls -la', 'remote', 'test')
        self.assertEqual('ssh test@remote "bash --login -c \'ls -la\'"', cmd)

        cmd = shell.format_remote_cmd('hdbnsutil -sr_enable --name=PRAGUE', 'remote', 'prdadm')
        self.assertEqual(
            'ssh prdadm@remote "bash --login -c \'hdbnsutil -sr_enable --name=PRAGUE\'"', cmd)

    def test_format_remote_cmd_error(self):
        with self.assertRaises(ValueError) as err:
            shell.format_remote_cmd('ls -la', 'remote', None)
        self.assertTrue('user must be provided' in str(err.exception))

    def test_execute_cmd_popen(self):
        # This test is used to check popen correct usage
        result = shell.execute_cmd('ls -la')
        self.assertEqual(result.returncode, 0)

    @mock.patch('shaptools.shell.ProcessResult')
    @mock.patch('subprocess.Popen')
    @mock.patch('logging.Logger.debug')
    def test_execute_cmd(self, logger, mock_popen, mock_process):

        mock_popen_inst = mock.Mock()
        mock_popen_inst.returncode = 5
        mock_popen_inst.communicate.return_value = (b'out', b'err')
        mock_popen.return_value = mock_popen_inst

        mock_process_inst = mock.Mock()
        mock_process.return_value = mock_process_inst

        result = shell.execute_cmd('ls -la')

        logger.assert_called_once_with(
            'Executing command "%s" with user %s', 'ls -la', None)

        mock_popen.assert_called_once_with(
            ['ls', '-la'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        mock_popen_inst.communicate.assert_called_once_with(input=None)

        mock_process.assert_called_once_with('ls -la', 5, b'out', b'err')

        self.assertEqual(mock_process_inst, result)

    @mock.patch('shaptools.shell.format_remote_cmd')
    @mock.patch('shaptools.shell.ProcessResult')
    @mock.patch('subprocess.Popen')
    @mock.patch('logging.Logger.debug')
    def test_execute_cmd_remote(
            self, logger, mock_popen, mock_process, mock_format):

        mock_format.return_value = 'updated command'

        mock_popen_inst = mock.Mock()
        mock_popen_inst.returncode = 5
        mock_popen_inst.communicate.return_value = (b'out', b'err')
        mock_popen.return_value = mock_popen_inst

        mock_process_inst = mock.Mock()
        mock_process.return_value = mock_process_inst

        result = shell.execute_cmd('ls -la', 'test', 'pass', 'remote')

        logger.assert_has_calls([
            mock.call('Executing command "%s" with user %s', 'ls -la', 'test'),
            mock.call('Command updated to "%s"', 'updated command')
        ])

        mock_format.assert_called_once_with('ls -la', 'remote', 'test')

        mock_popen.assert_called_once_with(
            ['updated', 'command'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        mock_popen_inst.communicate.assert_called_once_with(input=b'pass')

        mock_process.assert_called_once_with('updated command', 5, b'out', b'err')

        self.assertEqual(mock_process_inst, result)

    @mock.patch('shaptools.shell.format_su_cmd')
    @mock.patch('shaptools.shell.ProcessResult')
    @mock.patch('subprocess.Popen')
    @mock.patch('logging.Logger.debug')
    def test_execute_cmd_user(
            self, logger, mock_popen, mock_process, mock_format):

        mock_format.return_value = 'updated command'

        mock_popen_inst = mock.Mock()
        mock_popen_inst.returncode = 5
        mock_popen_inst.communicate.return_value = (b'out', b'err')
        mock_popen.return_value = mock_popen_inst

        mock_process_inst = mock.Mock()
        mock_process.return_value = mock_process_inst

        result = shell.execute_cmd('ls -la', 'test', 'pass')

        logger.assert_has_calls([
            mock.call('Executing command "%s" with user %s', 'ls -la', 'test'),
            mock.call('Command updated to "%s"', 'updated command')
        ])

        mock_popen.assert_called_once_with(
            ['updated', 'command'], stdout=subprocess.PIPE, stdin=subprocess.PIPE,
            stderr=subprocess.PIPE)

        mock_popen_inst.communicate.assert_called_once_with(input=b'pass')

        mock_process.assert_called_once_with('updated command', 5, b'out', b'err')

        self.assertEqual(mock_process_inst, result)

    @mock.patch('os.path')
    def test_create_ssh_askpass(self, mock_path):

        mock_path.dirname.return_value = 'file'
        mock_path.join.return_value = 'file/support/ssh_askpass'

        result = shell.create_ssh_askpass('pass', 'my_command')

        self.assertEqual(
            'export SSH_ASKPASS=file/support/ssh_askpass;export PASS=pass;export DISPLAY=:0;setsid my_command',
            result)

    @mock.patch('shaptools.shell.execute_cmd')
    def test_remove_user(self, mock_execute_cmd):

        result = mock.Mock(returncode=0)
        mock_execute_cmd.return_value = result

        shell.remove_user('user', False, 'root', 'pass', 'remote_host')

        mock_execute_cmd.assert_called_once_with('userdel user', 'root', 'pass', 'remote_host')

    @mock.patch('shaptools.shell.execute_cmd')
    def test_remove_user_force(self, mock_execute_cmd):

        result1 = mock.Mock(returncode=1, err='userdel: user user is currently used by process 1')
        result2 = mock.Mock(returncode=1, err='userdel: user user is currently used by process 2')
        result3 = mock.Mock(returncode=0)
        mock_execute_cmd.side_effect = [result1, None, result2, None, result3]

        shell.remove_user('user', True, 'root', 'pass')

        mock_execute_cmd.assert_has_calls([
            mock.call('userdel user', 'root', 'pass', None),
            mock.call('kill -9 1', 'root', 'pass', None),
            mock.call('userdel user', 'root', 'pass', None),
            mock.call('kill -9 2', 'root', 'pass', None),
            mock.call('userdel user', 'root', 'pass', None),
        ])

    @mock.patch('shaptools.shell.execute_cmd')
    def test_remove_user_error(self, mock_execute_cmd):

        result = mock.Mock(returncode=1)
        mock_execute_cmd.return_value = result

        with self.assertRaises(shell.ShellError) as err:
            shell.remove_user('user', False, 'root', 'pass')

        mock_execute_cmd.assert_called_once_with('userdel user', 'root', 'pass', None)
        self.assertTrue('error removing user user' in str(err.exception))

    @mock.patch('shaptools.shell.execute_cmd')
    def test_remove_user_force_error(self, mock_execute_cmd):

        result1 = mock.Mock(returncode=1, err='userdel: user user is currently used by process 1')
        result2 = mock.Mock(returncode=1, err='other error')
        result3 = mock.Mock(returncode=0)
        mock_execute_cmd.side_effect = [result1, None, result2, None, result3]

        with self.assertRaises(shell.ShellError) as err:
            shell.remove_user('user', True, 'root', 'pass')

        mock_execute_cmd.assert_has_calls([
            mock.call('userdel user', 'root', 'pass', None),
            mock.call('kill -9 1', 'root', 'pass', None),
            mock.call('userdel user', 'root', 'pass', None)
        ])
        self.assertTrue('error removing user user' in str(err.exception))
