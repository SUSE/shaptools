"""
Unitary tests for saputils.py.

:author: sisingh
:organization: SUSE LLC
:contact: sisingh@suse.com

:since: 2020-03-26
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
import unittest

try:
    from unittest import mock
except ImportError:
    import mock


from shaptools import saputils

class TestSapUtils(unittest.TestCase):
    """
    Unitary tests for shaptools/saputis.py.
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

    @mock.patch('shaptools.shell.execute_cmd')
    @mock.patch('os.path.isfile')
    def test_extract_sapcar_file(self, mock_sapcar_file, mock_execute_cmd):
        proc_mock = mock.Mock()
        proc_mock.returncode = 0
        mock_sapcar_file.side_effect = [True, True]
        mock_execute_cmd.return_value = proc_mock

        result = saputils.extract_sapcar_file(
            sapcar_exe='/sapmedia/sapcar.exe', sar_file='/sapmedia/IMDB_SERVER_LINUX.SAR',
            output_dir='/sapmedia/HANA', options='-v')
        
        cmd = '/sapmedia/sapcar.exe -xvf /sapmedia/IMDB_SERVER_LINUX.SAR -v -R /sapmedia/HANA'
        mock_execute_cmd.assert_called_once_with(cmd, user=None, password=None, remote_host=None)
        self.assertEqual(proc_mock, result)

    @mock.patch('shaptools.shell.execute_cmd')
    @mock.patch('os.path.isfile')
    def test_extract_sapcar_error(self, mock_sapcar_file, mock_execute_cmd):
        mock_sapcar_file.side_effect = [True, True]
        proc_mock = mock.Mock()
        proc_mock.returncode = 1
        mock_execute_cmd.return_value = proc_mock

        with self.assertRaises(saputils.SapUtilsError) as err:
            saputils.extract_sapcar_file(
               sapcar_exe='/sapmedia/sapcar.exe', sar_file='/sapmedia/IMDB_SERVER_LINUX.SAR')

        cmd = '/sapmedia/sapcar.exe -xvf /sapmedia/IMDB_SERVER_LINUX.SAR'
        mock_execute_cmd.assert_called_once_with(cmd, user=None, password=None, remote_host=None)
        
        self.assertTrue(
            'Error running SAPCAR command' in str(err.exception))

    @mock.patch('os.path.isfile')
    def test_extract_sapcar_FileDoesNotExistError(self, mock_sapcar_file):
        mock_sapcar_file.return_value = False

        with self.assertRaises(saputils.FileDoesNotExistError) as err:
            saputils.extract_sapcar_file(
               sapcar_exe='/sapmedia/sapcar.exe', sar_file='/sapmedia/IMDB_SERVER_LINUX.SAR')

        self.assertTrue(
            'SAPCAR executable \'{}\' does not exist'.format('/sapmedia/sapcar.exe') in str(err.exception))

    @mock.patch('os.path.isfile')
    def test_extract_sar_FileDoesNotExistError(self, mock_sar_file):
        mock_sar_file.side_effect = [True, False]

        with self.assertRaises(saputils.FileDoesNotExistError) as err:
            saputils.extract_sapcar_file(
                sapcar_exe='/sapmedia/sapcar.exe', sar_file='/sapmedia/IMDB_SERVER_LINUX.SAR')

        self.assertTrue(
            'The SAR file \'{}\' does not exist'.format('/sapmedia/IMDB_SERVER_LINUX.SAR') in str(err.exception))