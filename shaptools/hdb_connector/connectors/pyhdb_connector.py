"""
SAP HANA database connector using pyhdb open sourced package

How to install:
https://github.com/SAP/PyHDB

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-08
"""

import socket
import pyhdb

from shaptools.hdb_connector.connectors import base_connector


class PyhdbConnector(base_connector.BaseConnector):
    """
    Class to manage pyhdb connection and queries
    """

    def __init__(self):
        super(PyhdbConnector, self).__init__()
        self._logger.info('pyhdb package loaded')

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
        self._logger.info('connecting to SAP HANA database at %s:%s', host, port)
        try:
            self._connection = pyhdb.connect(
                host=host,
                port=port,
                user=kwargs.get('user'),
                password=kwargs.get('password'),
            )
        except socket.error as err:
            raise base_connector.ConnectionError('connection failed: {}'.format(err))
        self._logger.info('connected successfully')

    def query(self, sql_statement):
        """
        Query a sql query result and return a result object
        """
        self._logger.info('executing sql query: %s', sql_statement)
        try:
            cursor = None
            cursor = self._connection.cursor()
            cursor.execute(sql_statement)
            result = base_connector.QueryResult.load_cursor(cursor)
        except pyhdb.exceptions.DatabaseError as err:
            raise base_connector.QueryError('query failed: {}'.format(err))
        finally:
            if cursor:
                cursor.close()
        return result

    def disconnect(self):
        """
        Disconnect from SAP HANA database
        """
        self._logger.info('disconnecting from SAP HANA database')
        self._connection.close()
        self._logger.info('disconnected successfully')
