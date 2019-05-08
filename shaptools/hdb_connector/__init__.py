"""
SAP HANA database connector factory

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-05-08
"""

try:
    from shaptools.hdb_connector.connectors import dbapi_connector
    API = 'dbapi'
except ImportError:
    from shaptools.hdb_connector.connectors import pyhdb_connector
    API = 'pyhdb'
except:
    from shaptools.hdb_connector.connectors import base_connector
    raise base_connector.DriverNotAvailableError('dbapi nor pyhdb are installed')


class HdbConnector(object):
    """
    HDB factory connector
    """

    def __new__(cls):
        if API == 'dbapi':
            return dbapi_connector.DbapiConnector()
        elif API == 'pyhdb':
            return pyhdb_connector.PyhdbConnector()
        raise base_connector.DriverNotAvailableError('dbapi nor pyhdb are installed')
