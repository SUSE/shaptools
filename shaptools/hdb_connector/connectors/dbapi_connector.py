"""
SAP HANA database connector using official dbapi package

How to install:
https://help.sap.com/viewer/1efad1691c1f496b8b580064a6536c2d/Cloud/en-US/39eca89d94ca464ca52385ad50fc7dea.html

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-08
"""

from hdbcli import dbapi

from shaptools.hdb_connector.connectors import base_connector


class DbapiConnector(base_connector.BaseConnector):
    """
    Class to manage dbapi connection and queries
    """

    def __init__(self):
        super(DbapiConnector, self).__init__()
        self._logger.info('dbapi package loaded')

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
            self._connection = dbapi.connect(
                address=host,
                port=port,
                user=kwargs.get('user'),
                password=kwargs.get('password'),
            )
        except dbapi.Error as err:
            raise base_connector.ConnectionError('connection failed: {}'.format(err))
        self._logger.info('connected successfully')

    def query(self, sql_statement):
        """
        Query a sql query result and return a result object
        """
        self._logger.info('executing sql query: %s', sql_statement)
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(sql_statement)
                result = base_connector.QueryResult.load_cursor(cursor)
        except dbapi.Error as err:
            raise base_connector.QueryError('query failed: {}'.format(err))
        return result

    def disconnect(self):
        """
        Disconnect from SAP HANA database
        """
        self._logger.info('disconnecting from SAP HANA database')
        self._connection.close()
        self._logger.info('disconnected successfully')
