"""
Unitary tests for hdb_connector/__init__.py.

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

from shaptools.hdb_connector.connectors import base_connector

class TestInit(unittest.TestCase):
    """
    Unitary tests for __init__.py.
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

    def test_error(self):
        from shaptools import hdb_connector
        with self.assertRaises(base_connector.DriverNotAvailableError) as err:
            hdb_connector.HdbConnector()
        self.assertTrue('dbapi nor pyhdb are installed' in str(err.exception))
