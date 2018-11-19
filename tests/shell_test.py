"""
Unitary tests for shell.py.

:author: xarbulu
:organization: SUSE Linux GmbH
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
    def test_show_output(self, logger_error, logger_info):

        out = (b"Output text\n"
               b"line1\n"
               b"line2")

        err = (b"Error text\n"
               b"err1\n"
               b"err2")

        proc = shell.ProcessResult('test', 5, out, err)
        proc.show_output()

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

        out = b""

        err = b""

        proc = shell.ProcessResult('test', 5, out, err)
        proc.show_output()

        self.assertEqual(0, logger_info.call_count)
        self.assertEqual(0, logger_error.call_count)

    def test_find_pattern(self):

        out = (b"Output text\n"
               b"  line1  \n"
               b"line2")
        err = b""

        proc = shell.ProcessResult('test', 5, out, err)
        result = proc.find_pattern('.*line1.*')
        self.assertTrue(result)

    def test_find_pattern_false(self):

        out = (b"Output text\n"
               b"  line1  \n"
               b"line2")
        err = b""

        proc = shell.ProcessResult('test', 5, out, err)
        result = proc.find_pattern('.*line3.*')
        self.assertFalse(result)

    def test_format_su_cmd(self):
        cmd = shell.format_su_cmd('ls -la', 'test')
        self.assertEqual('su -lc "ls -la" test', cmd)

        cmd = shell.format_su_cmd('hdbnsutil -sr_enable --name=PRAGUE', 'prdadm')
        self.assertEqual('su -lc "hdbnsutil -sr_enable --name=PRAGUE" prdadm', cmd)

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

        mock_process_inst.show_output.assert_called_once_with()

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

        mock_process_inst.show_output.assert_called_once_with()

        self.assertEqual(mock_process_inst, result)
