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
        self._conn.connect('host', 1234, user='user', password='pass', timeout=1)
        mock_pyhdb.connect.assert_called_once_with(
            host='host', port=1234, user='user', password='pass')
        mock_logger.assert_has_calls([
            mock.call('connecting to SAP HANA database at %s:%s', 'host', 1234),
            mock.call('connected successfully')
        ])
        self.assertEqual(self._conn._connection.timeout, 1)

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.socket')
    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_connect_socket_error(self, mock_logger, mock_pyhdb, mock_socket):
        mock_socket.error = Exception
        mock_pyhdb.exceptions.DatabaseError = Exception
        mock_pyhdb.connect.side_effect = mock_socket.error('socket error')
        with self.assertRaises(self._pyhdb_connector.base_connector.ConnectionError) as err:
            self._conn.connect('host', 1234, user='user', password='pass')

        self.assertTrue('connection failed: {}'.format('socket error') in str(err.exception))
        mock_pyhdb.connect.assert_called_once_with(
            host='host', port=1234, user='user', password='pass')

        mock_logger.assert_called_once_with(
            'connecting to SAP HANA database at %s:%s', 'host', 1234)

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.socket')
    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_connect_pyhdb_error(self, mock_logger, mock_pyhdb, mock_socket):
        mock_socket.error = Exception
        mock_pyhdb.exceptions.DatabaseError = Exception
        mock_pyhdb.connect.side_effect = mock_pyhdb.exceptions.DatabaseError('pyhdb error')
        with self.assertRaises(self._pyhdb_connector.base_connector.ConnectionError) as err:
            self._conn.connect('host', 1234, user='user', password='pass')

        self.assertTrue('connection failed: {}'.format('pyhdb error') in str(err.exception))
        mock_pyhdb.connect.assert_called_once_with(
            host='host', port=1234, user='user', password='pass')

        mock_logger.assert_called_once_with(
            'connecting to SAP HANA database at %s:%s', 'host', 1234)

    @mock.patch('shaptools.hdb_connector.connectors.base_connector.QueryResult')
    @mock.patch('logging.Logger.info')
    def test_query(self, mock_logger, mock_result):

        mock_cursor = mock.Mock()
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.return_value = mock_cursor

        mock_result_inst = mock.Mock()
        mock_result_inst.records = ['data1', 'data2']
        mock_result_inst.metadata = 'metadata'
        mock_result.load_cursor.return_value = mock_result_inst

        result = self._conn.query('query')

        mock_cursor.execute.assert_called_once_with('query')
        mock_result.load_cursor.assert_called_once_with(mock_cursor)

        self.assertEqual(result.records, ['data1', 'data2'])
        self.assertEqual(result.metadata, 'metadata')
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')
        mock_cursor.close.assert_called_once_with()

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_query_error(self, mock_logger, mock_pyhdb):
        mock_pyhdb.exceptions.DatabaseError = Exception
        self._conn._connection = mock.Mock()
        self._conn._connection.cursor.side_effect = Exception('error')
        with self.assertRaises(self._pyhdb_connector.base_connector.QueryError) as err:
            self._conn.query('query')

        self.assertTrue('query failed: {}'.format('error') in str(err.exception))
        self._conn._connection.cursor.assert_called_once_with()
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_query_error_execute(self, mock_logger, mock_pyhdb):
        mock_pyhdb.exceptions.DatabaseError = Exception
        self._conn._connection = mock.Mock()
        cursor_mock = mock.Mock()
        self._conn._connection.cursor.return_value = cursor_mock
        cursor_mock.execute = mock.Mock()
        cursor_mock.execute.side_effect = Exception('error')
        with self.assertRaises(self._pyhdb_connector.base_connector.QueryError) as err:
            self._conn.query('query')

        self.assertTrue('query failed: {}'.format('error') in str(err.exception))
        self._conn._connection.cursor.assert_called_once_with()
        mock_logger.assert_called_once_with('executing sql query: %s', 'query')
        cursor_mock.close.assert_called_once_with()

    @mock.patch('logging.Logger.info')
    def test_disconnect(self, mock_logger):
        self._conn._connection = mock.Mock()
        self._conn.disconnect()
        self._conn._connection.close.assert_called_once_with()
        mock_logger.assert_has_calls([
            mock.call('disconnecting from SAP HANA database'),
            mock.call('disconnected successfully')
        ])

    def test_isconnected_false(self):
        self._conn._connection = None
        self.assertFalse(self._conn.isconnected())

        self._conn._connection = mock.Mock()
        self._conn._connection.isconnected.return_value = False
        self.assertFalse(self._conn.isconnected())

    @mock.patch('logging.Logger.error')
    def test_isconnected_error(self, logger):
        self._conn._connection = mock.Mock()
        self._conn._connection.isconnected.return_value = True
        self._conn._connection._socket = mock.Mock()
        self._conn._connection._socket.getpeername.side_effect = OSError('error')

        self.assertFalse(self._conn.isconnected())
        logger.assert_called_once_with('socket is not correctly working. closing socket')
        self.assertEqual(self._conn._connection._socket, None)

    def test_isconnected_correct(self):
        self._conn._connection = mock.Mock()
        self._conn._connection.isconnected.return_value = True
        self._conn._connection._socket = mock.Mock()
        self._conn._connection._socket.getpeername.return_value = 'data'

        self.assertTrue(self._conn.isconnected())

    def test_reconnect_notconnected(self):
        self._conn._connection = None
        with self.assertRaises(self._pyhdb_connector.base_connector.ConnectionError) as err:
            self._conn.reconnect()
        self.assertTrue('connect method must be used first to reconnect' in str(err.exception))

    @mock.patch('logging.Logger.info')
    def test_reconnect_connected(self, logger):
        self._conn._connection = mock.Mock()
        self._conn.isconnected = mock.Mock(return_value=True)
        self._conn.reconnect()
        logger.assert_called_once_with('connection already created')

    @mock.patch('logging.Logger.info')
    def test_reconnect(self, logger):
        self._conn._connection = mock.Mock()
        self._conn.isconnected = mock.Mock(return_value=False)
        self._conn.reconnect()

        self._conn._connection.connect.assert_called_once_with()
        logger.assert_called_once_with('reconnecting...')
        self.assertEqual(self._conn._connection.session_id, -1)
        self.assertEqual(self._conn._connection.packet_count, -1)

    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.socket')
    @mock.patch('shaptools.hdb_connector.connectors.pyhdb_connector.pyhdb')
    @mock.patch('logging.Logger.info')
    def test_reconnect_connect_error(self, logger, mock_pyhdb, mock_socket):
        mock_socket.error = Exception
        mock_pyhdb.exceptions.DatabaseError = Exception
        self._conn._connection = mock.Mock()
        self._conn.isconnected = mock.Mock(return_value=False)
        self._conn._connection.connect.side_effect = mock_socket.error('socket error')

        with self.assertRaises(self._pyhdb_connector.base_connector.ConnectionError) as err:
            self._conn.reconnect()
        self.assertTrue('socket error' in str(err.exception))

        self._conn._connection.connect.assert_called_once_with()
        logger.assert_called_once_with('reconnecting...')
        self.assertEqual(self._conn._connection.session_id, -1)
        self.assertEqual(self._conn._connection.packet_count, -1)
