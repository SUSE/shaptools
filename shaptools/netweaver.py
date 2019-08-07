"""
SAP Netweaver management module

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2010-07-30
"""

import logging

from shaptools import shell

# python2 and python3 compatibility for string usage
try:
    basestring
except NameError:  # pragma: no cover
    basestring = str


class NetweaverError(Exception):
    """
    Error during Netweaver command execution
    """


class NetweaverInstance(object):
    """
    SAP Netweaver instance implementation

    Args:
        sid (str): SAP Netweaver sid
        inst (str): SAP Netweaver instance number
        password (str): Netweaver instance password
    """

    # SID is usualy written uppercased, but the OS user is always created lower case.
    NETWEAVER_USER = '{sid}adm'.lower()
    UNINSTALL_PRODUCT = 'NW_Uninstall:GENERIC.IND.PD'
    GETPROCESSLIST_SUCCESS_CODES = [0, 3, 4]

    def __init__(self, sid, inst, password):
        # Force instance nr always with 2 positions.
        inst = '{:0>2}'.format(inst)
        if not all(isinstance(i, basestring) for i in [sid, inst, password]):
            raise TypeError(
                'provided sid, inst and password parameters must be str type')

        self._logger = logging.getLogger('{}{}'.format(sid, inst))
        self.sid = sid
        self.inst = inst
        self._password = password

    def _execute_sapcontrol(self, sapcontrol_function, exception=True):
        """
        Execute sapcontrol commands and return result

        Args:
            sapcontrol_function (str): sapcontrol function
            exception (boolean): Raise NetweaverError non-zero return code (default true)

        Returns:
            ProcessResult: ProcessResult instance storing subprocess returncode,
                stdout and stderr
        """
        user = self.NETWEAVER_USER.format(sid=self.sid)
        cmd = 'sapcontrol -nr {instance} -function {sapcontrol_function}'.format(
            instance=self.inst, sapcontrol_function=sapcontrol_function)
        result = shell.execute_cmd(cmd, user, self._password)

        if exception and result.returncode != 0:
            raise NetweaverError('Error running sapcontrol command: {}'.format(result.cmd))

        return result

    @staticmethod
    def _is_ascs_installed(processes):
        """
        Check if ASCS instance is installed
        """
        msg_server = shell.find_pattern(r'msg_server, MessageServer,.*', processes.output)
        enserver = shell.find_pattern(r'enserver, EnqueueServer,', processes.output)
        return bool(msg_server and enserver)

    @staticmethod
    def _is_ers_installed(processes):
        """
        Check if ERS instance is installed
        """
        msg_server = shell.find_pattern(r'enrepserver, EnqueueReplicator.*', processes.output)
        return bool(msg_server)

    def is_installed(self, sap_instance=None):
        """
        Check if SAP Netweaver is installed

        Args:
            sap_instance (str): SAP instance type. Available options: ascs
                If None, if any NW installation is existing will be checked

        Returns:
            bool: True if SAP instance is installed, False otherwise
        """
        processes = self.get_process_list(False)
        # TODO: Might be done using a dictionary to store the methods and keys
        if processes.returncode not in self.GETPROCESSLIST_SUCCESS_CODES:
            return False
        elif not sap_instance:
            return True
        elif sap_instance == 'ascs':
            return self._is_ascs_installed(processes)
        elif sap_instance == 'ers':
            return self._is_ers_installed(processes)
        else:
            raise ValueError('provided sap instance type is not valid: {}'.format(sap_instance))

    @classmethod
    def install(cls, software_path, virtual_host, product_id, conf_file, root_user, password):
        """
        Install SAP Netweaver instance

        Args:
            software_path (str): Path where SAP Netweaver 'sapinst' tool is located
            conf_file (str): Path to the configuration file
            root_user (str): Root user name
            password (str): Root user password
        """

        cmd = '{software_path}/sapinst SAPINST_USE_HOSTNAME={virtual_host} '\
            'SAPINST_EXECUTE_PRODUCT_ID={product_id} '\
            'SAPINST_SKIP_SUCCESSFULLY_FINISHED_DIALOG=true SAPINST_START_GUISERVER=false '\
            'SAPINST_INPUT_PARAMETERS_URL={conf_file}'.format(
                software_path=software_path,
                virtual_host=virtual_host,
                product_id=product_id,
                conf_file=conf_file)
        result = shell.execute_cmd(cmd, root_user, password)
        if result.returncode:
            raise NetweaverError('SAP Netweaver installation failed')

    def uninstall(self, software_path, virtual_host, conf_file, root_user, password):
        """
        Uninstall SAP Netweaver instance

        Args:
            software_path (str): Path where SAP Netweaver 'sapinst' tool is located
            conf_file (str): Path to the configuration file
            root_user (str): Root user name
            password (str): Root user password
        """
        user = self.NETWEAVER_USER.format(sid=self.sid)
        self.install(
            software_path, virtual_host, self.UNINSTALL_PRODUCT, conf_file, root_user, password)
        shell.remove_user(user, True, root_user, password)

    def get_process_list(self, exception=True):
        """
        Get SAP processes list
        """
        result = self._execute_sapcontrol('GetProcessList', exception=False)
        if exception and result.returncode not in self.GETPROCESSLIST_SUCCESS_CODES:
            raise NetweaverError('Error running sapcontrol command: {}'.format(result.cmd))

        return result
