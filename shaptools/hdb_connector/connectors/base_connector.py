"""
Base connector

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-08
"""

import logging


class BaseError(Exception):
    """
    Base exception
    """


class DriverNotAvailableError(Exception):
    """
    dbapi nor pyhdb are installed
    """


class ConnectionError(Exception):
    """
    Error during connection
    """


class QueryError(BaseError):
    """
    Error during query
    """


class BaseConnector(object):
    """
    Base SAP HANA database connector
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._connection = None

    def connect(self, host, port=30015, **kwargs):
        """
        Connect to the SAP HANA database

        # TODO: Add option to connect using the key
        # TODO: Add encryption options

        Args:
            host (str): Host where the database is running
            port (int): Database port (3{inst_number}15 by default)
            user (str): Existing username in the database
            password (str): User password
        """
        raise NotImplementedError(
            'method must be implemented in inherited connectors')

    def query(self, sql_statement):
        """
        Query a sql statement and return response
        """
        raise NotImplementedError(
            'method must be implemented in inherited connectors')

    def disconnect(self):
        """
        Disconnecto from SAP HANA database
        """
        raise NotImplementedError(
            'method must be implemented in inherited connectors')
