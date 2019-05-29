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

class QueryResult(object):
    """
    Class to manage query results

    Args:
        records (list of tuples): rows of a query result
        metadata (tuple): Sequence of 7-item sequences that describe one result column
    """

    def __init__(self, records, metadata):
        self._logger = logging.getLogger(__name__)
        self.records = records
        self.metadata = metadata

    @classmethod
    def load_cursor(cls, cursor):
        """
        load cursor and extract records and metadata

        Args:
            cursor (obj): Cursor object created by the connector (dbapi or pydhb)
        """
        records = cursor.fetchall() # TODO: catch any exceptions raised by fetchall()
        metadata = cursor.description
        instance = cls(records, metadata)
        instance._logger.info('query records: %s', instance.records)
        return instance

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
        Disconnect from SAP HANA database
        """
        raise NotImplementedError(
            'method must be implemented in inherited connectors')
