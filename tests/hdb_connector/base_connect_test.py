"""
Unitary tests for hdb_connector/connector/base_connector.py.

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


class TestQueryResul(unittest.TestCase):
    """
    Unitary tests for base_connector.py QueryResult class
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)
        from shaptools.hdb_connector.connectors import base_connector
        cls._base_connector = base_connector

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
    def test_load_cursor(self, logger):
        mock_cursor = mock.Mock()
        mock_cursor.description = 'metadata'
        mock_cursor.fetchall.return_value = ['data1', 'data2']
        result = self._base_connector.QueryResult.load_cursor(mock_cursor)
        logger.assert_called_once_with('query records: %s', ['data1', 'data2'])
        self.assertEqual(result.records, ['data1', 'data2'])
        self.assertEqual(result.metadata, 'metadata')


class TestHana(unittest.TestCase):
    """
    Unitary tests for base_connector.py BaseConnector class
    """

    @classmethod
    def setUpClass(cls):
        """
        Global setUp.
        """

        logging.basicConfig(level=logging.INFO)
        sys.modules['hdbcli'] = mock.Mock()
        sys.modules['pyhdb'] = mock.Mock()

        from shaptools.hdb_connector.connectors import base_connector
        cls._base_connector = base_connector

    def setUp(self):
        """
        Test setUp.
        """
        self._conn = self._base_connector.BaseConnector()

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """
        sys.modules.pop('hdbcli')
        sys.modules.pop('pyhdb')

    def test_connect(self):
        with self.assertRaises(NotImplementedError) as err:
            self._conn.connect('host')
            self.assertTrue(
                'method must be implemented in inherited connectors'
                in str(err.exception))

    def test_query(self):
        with self.assertRaises(NotImplementedError) as err:
            self._conn.query('query')
            self.assertTrue(
                'method must be implemented in inherited connectors'
                in str(err.exception))

    def test_disconnect(self):
        with self.assertRaises(NotImplementedError) as err:
            self._conn.disconnect()
            self.assertTrue(
                'method must be implemented in inherited connectors'
                in str(err.exception))
