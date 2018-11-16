"""
Unitary tests for hana.py.

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

import mock

from shaptools import hana

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

    def tearDown(self):
        """
        Test tearDown.
        """

    @classmethod
    def tearDownClass(cls):
        """
        Global tearDown.
        """
