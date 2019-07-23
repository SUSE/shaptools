"""
Unitary tests for shaptools/shapcli.py.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2019-07-16
"""

# pylint:disable=C0103,C0111,W0212,W0611

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging

try:
    from unittest import mock
except ImportError:
    import mock

import pytest

from shaptools import shapcli


class TestShapCli(object):
    """
    Unitary tests for shaptools/shapcli.py.
    """

    def test_format(self):
        mock_record = mock.Mock(
            name='test',
            level=1,
            pathname='path',
            lineno=1,
            msg='msg',
            args=(),
            exc_info=None,
            exc_text=None,
            stack_info=None
        )
        mock_record.getMessage.return_value = 'msg'
        formatter = shapcli.DecodedFormatter()
        message = formatter.format(mock_record)
        assert message == 'msg'

        mock_record.getMessage.return_value = "b'msg'"
        formatter = shapcli.DecodedFormatter()
        message = formatter.format(mock_record)
        assert message == 'msg'

    @mock.patch('logging.getLogger')
    @mock.patch('logging.StreamHandler')
    @mock.patch('shaptools.shapcli.DecodedFormatter')
    def test_setup_logger(self, mock_formatter, mock_stream_handler, mock_get_logger):

        mock_logger_instance = mock.Mock()
        mock_get_logger.return_value = mock_logger_instance

        mock_stream_instance = mock.Mock()
        mock_stream_handler.return_value = mock_stream_instance

        mock_formatter_instance = mock.Mock()
        mock_formatter.return_value = mock_formatter_instance

        logger = shapcli.setup_logger('INFO')

        mock_formatter.assert_called_once_with(shapcli.LOGGING_FORMAT)
        mock_stream_handler.assert_called_once_with()
        mock_get_logger.assert_called_once_with()
        mock_stream_instance.setFormatter.assert_called_once_with(mock_formatter_instance)

        mock_logger_instance.addHandler.assert_called_once_with(mock_stream_instance)
        mock_logger_instance.setLevel.assert_called_once_with(level='INFO')

        assert logger == mock_logger_instance

    @mock.patch('shaptools.shapcli.json.load')
    @mock.patch('shaptools.shapcli.open')
    def test_config_data(self, mock_open, mock_json_load):

        mock_logger = mock.Mock()

        data = shapcli.ConfigData({'sid': 'prd', 'instance': '00', 'password': 'pass'}, mock_logger)

        assert data.sid == 'prd'
        assert data.instance == '00'
        assert data.password == 'pass'
        assert data.remote == None

        data = shapcli.ConfigData(
            {'sid': 'prd', 'instance': '00', 'password': 'pass', 'remote': 'host'}, mock_logger)

        assert data.sid == 'prd'
        assert data.instance == '00'
        assert data.password == 'pass'
        assert data.remote == 'host'

        with pytest.raises(KeyError) as err:
            shapcli.ConfigData({'sid': 'prd', 'instance': '00'}, mock_logger)

        mock_logger.error.assert_has_calls([
            mock.call('Configuration file must have the sid, instance and password entries')
        ])

    @mock.patch('argparse.ArgumentParser')
    @mock.patch('shaptools.shapcli.parse_hana_arguments')
    @mock.patch('shaptools.shapcli.parse_sr_arguments')
    def test_parse_arguments(
        self, mock_parse_sr_arguments, mock_parse_hana_arguments, mock_argument_parser):

        mock_argument_parser_instance = mock.Mock()
        mock_argument_parser.return_value = mock_argument_parser_instance
        mock_argument_parser_instance.parse_args.return_value = 'args'

        mock_subcommands = mock.Mock()
        mock_argument_parser_instance.add_subparsers.return_value = mock_subcommands

        mock_hana = mock.Mock()
        mock_sr = mock.Mock()
        mock_subcommands.add_parser.side_effect = [mock_hana, mock_sr]

        my_parser, my_args = shapcli.parse_arguments()

        mock_argument_parser.assert_called_once_with(shapcli.PROG)

        mock_argument_parser_instance.add_argument.assert_has_calls([
            mock.call('-v', '--verbosity',
                help='Python logging level. Options: DEBUG, INFO, WARN, ERROR (INFO by default)'),
            mock.call('-r', '--remote',
                help='Run the command in other machine using ssh'),
            mock.call('-c', '--config',
                help='JSON configuration file with SAP HANA instance data (sid, instance and password)'),
            mock.call('-s', '--sid',
                help='SAP HANA sid'),
            mock.call('-i', '--instance',
                help='SAP HANA instance'),
            mock.call('-p', '--password',
                help='SAP HANA password')
        ])

        assert mock_argument_parser_instance.add_argument.call_count == 6

        mock_argument_parser_instance.add_subparsers.assert_called_once_with(
            title='subcommands', description='valid subcommands', help='additional help')

        mock_subcommands.add_parser.assert_has_calls([
            mock.call('hana', help='Commands to interact with SAP HANA databse'),
            mock.call('sr', help='Commands to interact with SAP HANA system replication')
        ])

        mock_parse_sr_arguments.assert_called_once_with(mock_sr)
        mock_parse_hana_arguments.assert_called_once_with(mock_hana)

        mock_argument_parser_instance.parse_args.assert_called_once_with()

        assert my_parser == mock_argument_parser_instance
        assert my_args == 'args'

    def test_parse_hana_arguments(self):

        mock_subparser = mock.Mock()
        mock_subcommands = mock.Mock()
        mock_subparser.add_subparsers.return_value = mock_subcommands

        mock_dummy = mock.Mock()
        mock_hdbsql = mock.Mock()
        mock_user_key = mock.Mock()
        mock_backup = mock.Mock()

        mock_subcommands.add_parser.side_effect = [
            None, None, None, None, None, None, None, None, None,
            mock_dummy, mock_hdbsql, mock_user_key, mock_backup
        ]

        shapcli.parse_hana_arguments(mock_subparser)

        mock_subparser.add_subparsers.assert_called_once_with(
            title='hana', dest='hana', help='Commands to interact with SAP HANA databse')

        mock_subcommands.add_parser.assert_has_calls([
            mock.call('is_running', help='Check if SAP HANA database is running'),
            mock.call('version', help='Show SAP HANA database version'),
            mock.call('start', help='Start SAP HANA database'),
            mock.call('stop', help='Stop SAP HANA database'),
            mock.call('info', help='Show SAP HANA database information'),
            mock.call('kill', help='Kill all SAP HANA database processes'),
            mock.call('overview', help='Show SAP HANA database overview'),
            mock.call('landscape', help='Show SAP HANA database landscape'),
            mock.call('uninstall', help='Uninstall SAP HANA database instance'),
            mock.call('dummy', help='Get data from DUMMY table'),
            mock.call('hdbsql', help='Run a sql command with hdbsql'),
            mock.call('user', help='Create a new user key'),
            mock.call('backup', help='Create node backup')
        ])

        mock_dummy.add_argument.assert_has_calls([
            mock.call('--key_name',
                help='Keystore to connect to sap hana db '\
                '(if this value is set user, password and database are omitted'),
            mock.call('--user_name', help='User to connect to sap hana db'),
            mock.call('--user_password', help='Password to connect to sap hana db'),
            mock.call('--database', help='Database name to connect')
        ])

        mock_hdbsql.add_argument.assert_has_calls([
            mock.call('--key_name',
                help='Keystore to connect to sap hana db '\
                '(if this value is set user, password and database are omitted'),
            mock.call('--user_name', help='User to connect to sap hana db'),
            mock.call('--user_password', help='Password to connect to sap hana db'),
            mock.call('--database', help='Database name to connect'),
            mock.call('--query', help='Query to execute')
        ])

        mock_user_key.add_argument.assert_has_calls([
            mock.call('--key_name', help='Key name', required=True),
            mock.call('--environment', help='Database location (host:port)', required=True),
            mock.call('--user_name', help='User to connect to sap hana db', required=True),
            mock.call('--user_password', help='Password to connect to sap hana db', required=True),
            mock.call('--database', help='Database name to connect', required=True)
        ])

        mock_backup.add_argument.assert_has_calls([
            mock.call('--name', help='Backup file name', required=True),
            mock.call('--database', help='Database name to connect', required=True),
            mock.call('--key_name', help='Key name'),
            mock.call('--user_name', help='User to connect to sap hana db'),
            mock.call('--user_password', help='Password to connect to sap hana db')
        ])

    def test_parse_sr_arguments(self):

        mock_subparser = mock.Mock()
        mock_subcommands = mock.Mock()
        mock_subparser.add_subparsers.return_value = mock_subcommands

        mock_state = mock.Mock()
        mock_status = mock.Mock()
        mock_cleanup = mock.Mock()
        mock_enable= mock.Mock()
        mock_register = mock.Mock()
        mock_unregister= mock.Mock()
        mock_copy_ssfs= mock.Mock()

        mock_subcommands.add_parser.side_effect = [
            mock_state, mock_status, None, mock_cleanup, None, mock_enable,
            mock_register, mock_unregister, mock_copy_ssfs
        ]

        shapcli.parse_sr_arguments(mock_subparser)

        mock_subparser.add_subparsers.assert_called_once_with(
            title='sr', dest='sr', help='Commands to interact with SAP HANA system replication')

        mock_subcommands.add_parser.assert_has_calls([
            mock.call('state', help='Show SAP HANA system replication state'),
            mock.call('status', help='Show SAP HANAsystem replication status'),
            mock.call('disable', help='Disable SAP HANA system replication (to be executed in Primary node)'),
            mock.call('cleanup', help='Cleanup SAP HANA system replication'),
            mock.call('takeover', help='Perform a takeover operation (to be executed in Secondary node)'),
            mock.call('enable', help='Enable SAP HANA system replication primary site'),
            mock.call('register', help='Register SAP HANA system replication secondary site'),
            mock.call('unregister', help='Unegister SAP HANA system replication secondary site'),
            mock.call('copy_ssfs', help='Copy current node ssfs files to other host')
        ])

        mock_state.add_argument.assert_called_once_with(
            '--sapcontrol', help='Run with sapcontrol', action='store_true')

        mock_status.add_argument.assert_called_once_with(
            '--sapcontrol', help='Run with sapcontrol', action='store_true')

        mock_cleanup.add_argument.assert_called_once_with(
            '--force', help='Force the cleanup', action='store_true'),

        mock_enable.add_argument.assert_called_once_with(
            '--name', help='Primary site name', required=True)

        mock_register.add_argument.assert_has_calls([
            mock.call('--name', help='Secondary site name', required=True),
            mock.call('--remote_host', help='Primary site hostname', required=True),
            mock.call('--remote_instance', help='Primary site SAP HANA instance number', required=True),
            mock.call('--replication_mode', help='System replication replication mode', default='sync'),
            mock.call('--operation_mode', help='System replication operation mode', default='logreplay')
        ])

        mock_unregister.add_argument.assert_called_once_with(
            '--name', help='Primary site name', required=True)

        mock_copy_ssfs.add_argument.assert_has_calls([
            mock.call('--remote_host', help='Other host name', required=True),
            mock.call('--remote_password',
                help='Other host SAP HANA instance password (sid and instance must match '\
                'with the current host)', required=True)
        ])

    @mock.patch('shaptools.shapcli.input')
    def test_uninstall(self, mock_input):

        mock_hana_instance = mock.Mock(sid='prd', inst='00', _password='pass')
        mock_logger = mock.Mock()
        mock_input.return_value = 'y'

        shapcli.uninstall(mock_hana_instance, mock_logger)

        mock_input.assert_called_once_with()
        mock_logger.info.assert_called_once_with(
            'This command will uninstall SAP HANA instance '\
            'with sid %s and instance number %s (y/n): ', 'prd', '00')
        mock_hana_instance.uninstall.assert_called_once_with('prdadm', 'pass')

    @mock.patch('shaptools.shapcli.input')
    def test_uninstall_cancel(self, mock_input):

        mock_hana_instance = mock.Mock(sid='prd', inst='00', _password='pass')
        mock_logger = mock.Mock()
        mock_input.return_value = 'n'

        shapcli.uninstall(mock_hana_instance, mock_logger)

        mock_input.assert_called_once_with()
        mock_logger.info.assert_has_calls([
            mock.call(
                'This command will uninstall SAP HANA instance '\
                'with sid %s and instance number %s (y/n): ', 'prd', '00'),
            mock.call('Command execution canceled')
        ])

    def test_run_hdbsql(self):
        mock_hana_instance = mock.Mock(sid='prd', inst='00', _password='pass')
        args = mock.Mock(key_name='key', user_name='user', user_password='pass', database='db')

        mock_hana_instance._hdbsql_connect.return_value = 'hdbsql'

        shapcli.run_hdbsql(mock_hana_instance, args, 'cmd')

        mock_hana_instance._hdbsql_connect.assert_called_once_with(
            key_name='key', user_name='user', user_password='pass')

        mock_hana_instance._run_hana_command.assert_called_once_with(
            'hdbsql -d db \\"cmd\\"'
        )

    @mock.patch('shaptools.shapcli.run_hdbsql')
    @mock.patch('shaptools.shapcli.uninstall')
    def test_run_hana_subcommands(self, mock_uninstall, mock_run_hdbsql):

        mock_hana_instance = mock.Mock()
        mock_logger = mock.Mock()

        mock_hana_instance.is_running.return_value = 1
        mock_hana_args = mock.Mock(hana='is_running')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.is_running.assert_called_once_with()
        mock_logger.info.assert_called_once_with('SAP HANA database running state: %s', 1)

        mock_hana_args = mock.Mock(hana='version')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.get_version.assert_called_once_with()

        mock_hana_args = mock.Mock(hana='start')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.start.assert_called_once_with()

        mock_hana_args = mock.Mock(hana='stop')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.stop.assert_called_once_with()

        mock_hana_args = mock.Mock(hana='info')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance._run_hana_command.assert_called_once_with('HDB info')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(hana='kill')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance._run_hana_command.assert_called_once_with('HDB kill-9')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(hana='overview')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance._run_hana_command.assert_called_once_with('HDBSettings.sh systemOverview.py')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(hana='landscape')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance._run_hana_command.assert_called_once_with('HDBSettings.sh landscapeHostConfiguration.py')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(hana='uninstall')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_uninstall.assert_called_once_with(mock_hana_instance, mock_logger)

        mock_hana_args = mock.Mock(hana='dummy')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_run_hdbsql.assert_called_once_with(mock_hana_instance, mock_hana_args, 'SELECT * FROM DUMMY')
        mock_run_hdbsql.reset_mock()

        mock_hana_args = mock.Mock(hana='hdbsql', query='query')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_run_hdbsql.assert_called_once_with(mock_hana_instance, mock_hana_args, 'query')
        mock_run_hdbsql.reset_mock()

        mock_hana_args = mock.Mock(
            hana='user', key_name='key', environment='env',
            user_name='user', user_password='pass', database='db')
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.create_user_key.assert_called_once_with('key', 'env', 'user', 'pass', 'db')

        mock_hana_args = mock.Mock(
            hana='backup', database='db', key_name='key',
            user_name='user', user_password='pass')
        mock_hana_args.name = 'name'
        shapcli.run_hana_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.create_backup.assert_called_once_with('db', 'name', 'key', 'user', 'pass')

    def test_run_sr_subcommands(self):

        mock_hana_instance = mock.Mock()
        mock_logger = mock.Mock()

        mock_hana_args = mock.Mock(sr='state', sapcontrol=True)
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        cmd = 'hdbnsutil -sr_state --sapcontrol=1'
        mock_hana_instance._run_hana_command.assert_called_once_with(cmd)
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='state', sapcontrol=False)
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        cmd = 'hdbnsutil -sr_state'
        mock_hana_instance._run_hana_command.assert_called_once_with(cmd)
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='status', sapcontrol=True)
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        cmd = 'HDBSettings.sh systemReplicationStatus.py --sapcontrol=1'
        mock_hana_instance._run_hana_command.assert_called_once_with(cmd, exception=False)
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='status', sapcontrol=False)
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        cmd = 'HDBSettings.sh systemReplicationStatus.py'
        mock_hana_instance._run_hana_command.assert_called_once_with(cmd, exception=False)
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='disable')
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.sr_disable_primary.assert_called_once_with()

        mock_hana_args = mock.Mock(sr='cleanup', force=True)
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.sr_cleanup.assert_called_once_with(True)

        mock_hana_args = mock.Mock(sr='takeover')
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance._run_hana_command.assert_called_once_with('hdbnsutil -sr_takeover')
        mock_hana_instance.reset_mock()
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='enable')
        mock_hana_args.name = 'primary'
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.sr_enable_primary.assert_called_once_with('primary')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(
            sr='register', remote_host='remote', remote_instance='00',
            replication_mode='repl', operation_mode='oper')
        mock_hana_args.name = 'secondary'
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.sr_register_secondary.assert_called_once_with(
            'secondary', 'remote', '00', 'repl', 'oper')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='unregister')
        mock_hana_args.name = 'secondary'
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.sr_unregister_secondary.assert_called_once_with('secondary')
        mock_hana_instance.reset_mock()

        mock_hana_args = mock.Mock(sr='copy_ssfs', remote_host='remote', remote_password='pass')
        shapcli.run_sr_subcommands(mock_hana_instance, mock_hana_args, mock_logger)
        mock_hana_instance.copy_ssfs_files.assert_called_once_with('remote', 'pass')
        mock_hana_instance.reset_mock()

    @mock.patch('shaptools.shapcli.json.load')
    @mock.patch('shaptools.shapcli.open')
    def test_load_config_file(self, mock_open, mock_json_load):

        mock_logger = mock.Mock()
        mock_json_load.return_value = {'sid': 'prd', 'instance': '00', 'password': 'pass'}

        data = shapcli.load_config_file('config.json', mock_logger)
        assert data == {'sid': 'prd', 'instance': '00', 'password': 'pass'}

    @mock.patch('shaptools.shapcli.run_hana_subcommands')
    @mock.patch('shaptools.shapcli.hana.HanaInstance')
    @mock.patch('shaptools.shapcli.load_config_file')
    @mock.patch('shaptools.shapcli.setup_logger')
    @mock.patch('shaptools.shapcli.parse_arguments')
    def test_run_hana(
            self, mock_parse_arguments, mock_setup_logger,
            mock_load_config_file, mock_hana,
            mock_run_hana_subcommands):

        mock_parser = mock.Mock()
        mock_args = mock.Mock(verbosity='INFO', config='config.json', hana=True, remote=None)
        mock_logger = mock.Mock()
        mock_hana_instance = mock.Mock()
        mock_parse_arguments.return_value = [mock_parser, mock_args]
        mock_setup_logger.return_value = mock_logger
        mock_load_config_file.return_value = {
            'sid': 'prd', 'instance': '00', 'password': 'pass', 'remote': 'host'}
        mock_hana.return_value = mock_hana_instance

        shapcli.run()

        mock_parse_arguments.assert_called_once_with()
        mock_setup_logger.assert_called_once_with('INFO')
        mock_load_config_file.assert_called_once_with('config.json', mock_logger)
        mock_hana.assert_called_once_with('prd', '00', 'pass', remote_host='host')
        mock_run_hana_subcommands.assert_called_once_with(mock_hana_instance, mock_args, mock_logger)

    @mock.patch('shaptools.shapcli.run_sr_subcommands')
    @mock.patch('shaptools.shapcli.hana.HanaInstance')
    @mock.patch('shaptools.shapcli.setup_logger')
    @mock.patch('shaptools.shapcli.parse_arguments')
    def test_run_sr(
            self, mock_parse_arguments, mock_setup_logger,
            mock_hana, mock_run_sr_subcommands):

        mock_parser = mock.Mock()
        mock_args = mock.Mock(
            verbosity='INFO', config=False, sid='qas', instance='01', password='mypass',
            remote='remote', sr=True)
        mock_logger = mock.Mock()
        mock_hana_instance = mock.Mock()
        mock_parse_arguments.return_value = [mock_parser, mock_args]
        mock_setup_logger.return_value = mock_logger
        mock_hana.return_value = mock_hana_instance

        shapcli.run()

        mock_parse_arguments.assert_called_once_with()
        mock_setup_logger.assert_called_once_with('INFO')
        mock_hana.assert_called_once_with('qas', '01', 'mypass', remote_host='remote')
        mock_run_sr_subcommands.assert_called_once_with(mock_hana_instance, mock_args, mock_logger)

    @mock.patch('shaptools.shapcli.hana.HanaInstance')
    @mock.patch('shaptools.shapcli.setup_logger')
    @mock.patch('shaptools.shapcli.parse_arguments')
    def test_run_help(
            self, mock_parse_arguments, mock_setup_logger, mock_hana):

        mock_parser = mock.Mock()
        mock_args = mock.Mock(
            verbosity='INFO', config=False, sid='qas', instance='01', password='mypass', remote=None)
        mock_logger = mock.Mock()
        mock_hana_instance = mock.Mock()
        mock_parse_arguments.return_value = [mock_parser, mock_args]
        mock_setup_logger.return_value = mock_logger
        mock_hana.return_value = mock_hana_instance

        shapcli.run()

        mock_parse_arguments.assert_called_once_with()
        mock_setup_logger.assert_called_once_with('INFO')
        mock_hana.assert_called_once_with('qas', '01', 'mypass', remote_host=None)
        mock_parser.print_help.assert_called_once_with()


    @mock.patch('shaptools.shapcli.setup_logger')
    @mock.patch('shaptools.shapcli.parse_arguments')
    def test_run_sr_invalid_params(self, mock_parse_arguments, mock_setup_logger):

        mock_parser = mock.Mock()
        mock_args = mock.Mock(
            verbosity=False, config=False, sid='qas', instance='01', password=False, sr=True)
        mock_logger = mock.Mock()
        mock_hana_instance = mock.Mock()
        mock_parse_arguments.return_value = [mock_parser, mock_args]
        mock_setup_logger.return_value = mock_logger

        with pytest.raises(SystemExit) as my_exit:
            shapcli.run()

        assert my_exit.type == SystemExit
        assert my_exit.value.code == 1

        mock_parse_arguments.assert_called_once_with()
        mock_setup_logger.assert_called_once_with(logging.DEBUG)
        mock_logger.info.assert_called_once_with(
            'Configuration file or sid, instance and passwords parameters must be provided\n')
        mock_parser.print_help.assert_called_once_with()

    @mock.patch('shaptools.shapcli.run_sr_subcommands')
    @mock.patch('shaptools.shapcli.hana.HanaInstance')
    @mock.patch('shaptools.shapcli.setup_logger')
    @mock.patch('shaptools.shapcli.parse_arguments')
    def test_run_error(
            self, mock_parse_arguments, mock_setup_logger,
            mock_hana, mock_run_sr_subcommands):

        mock_parser = mock.Mock()
        mock_args = mock.Mock(
            verbosity='INFO', config=False, sid='qas', instance='01',
            password='mypass', sr=True, remote=None)
        mock_logger = mock.Mock()
        mock_hana_instance = mock.Mock()
        mock_parse_arguments.return_value = [mock_parser, mock_args]
        mock_setup_logger.return_value = mock_logger
        mock_hana.return_value = mock_hana_instance
        mock_run_sr_subcommands.side_effect = ValueError('my error')

        with pytest.raises(SystemExit) as my_exit:
            shapcli.run()

        assert my_exit.type == SystemExit
        assert my_exit.value.code == 1

        mock_parse_arguments.assert_called_once_with()
        mock_setup_logger.assert_called_once_with('INFO')
        mock_hana.assert_called_once_with('qas', '01', 'mypass', remote_host=None)
        mock_run_sr_subcommands.assert_called_once_with(mock_hana_instance, mock_args, mock_logger)
