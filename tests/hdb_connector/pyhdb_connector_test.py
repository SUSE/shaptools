"""
Unitary tests for hdb_connector/connector/pyhdb_connector.py.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-14
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
import logging
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from unittest import mock
except ImportError:
    import mock


class PyhdbException(Exception):
    """
    pyhdb.exceptions mock exception
    """


class TestHDBConnector(unittest.TestCase):
    """
    Unitary tests for pyhdb_connector.py.
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)
        sys.modules['pyhdb'] = mock.Mock()
        from shaptools.hdb_connector.connectors import pyhdb_connector
        cls._pyhdb_connector = pyhdb_connector

    def setUp(self):
        """
        Test setUp.
        """
        self._conn = self._pyhdb_connector.PyhdbConnector()

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """
        sys.modules.pop('pyhdb')

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_connect(self, mock_logger, mock_pyhdb):
        self._conn.connect('host', 1234, user='user', password='pass')
        mock_pyhdb.connect.assert_called_once_with(
            host='host', port=1234, user='user', password='pass')
        mock_logger.assert_has_calls([
            mock.call('connecting to SAP HANA database at %s:%s', 'host', 1234),
            mock.call('connected successfully')
        ])

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.socket')
    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_connect_error(self, mock_logger, mock_pyhdb, mock_socket):
        mock_socket.error = PyhdbException
        mock_pyhdb.connect.side_effect = mock_socket.error('error')
        with self.assertRaises(self._pyhdb_connector.base_connector.ConnectionError) as err:
            self._conn.connect('host', 1234, user='user', password='pass')

        self.assertTrue('connection failed: {}'.format('error') in str(err.exception))
        mock_pyhdb.connect.assert_called_once_with(
            host='host', port=1234, user='user', password='pass')

        mock_logger.assert_called_once_with(
            'connecting to SAP HANA database at %s:%s', 'host', 1234)

    @mock.patch('logging.Logger.info')
    def test_query(self, mock_logger):

        mock_cursor = mock.Mock()
        mock_cursor.fetchall.return_value = 'result'
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.return_value = mock_cursor

        response = self._conn.query('query')

        mock_cursor.execute.assert_called_once_with('query')
        mock_cursor.fetchall.assert_called_once_with()

        self.assertEqual(response.data, 'result')
        mock_logger.assert_has_calls([
            mock.call('executing sql query: %s', 'query'),
            mock.call('query result: %s', 'result')
        ])

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_query_error(self, mock_logger, mock_pyhdb):
        mock_pyhdb.exceptions.DatabaseError = PyhdbException
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.side_effect = mock_pyhdb.exceptions.DatabaseError('error')
        with self.assertRaises(self._pyhdb_connector.base_connector.QueryError) as err:
            self._conn.query('query')

        self.assertTrue('query failed: {}'.format('error') in str(err.exception))
        self._conn._connection.cursor.assert_called_once_with()
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')

    @mock.patch('logging.Logger.info')
    def test_disconnect(self, mock_logger):
        self._conn._connection = mock.Mock()
        self._conn.disconnect()
        self._conn._connection.close.assert_called_once_with()
        mock_logger.assert_has_calls([
            mock.call('disconnecting from SAP HANA database'),
            mock.call('disconnected successfully')
        ])
