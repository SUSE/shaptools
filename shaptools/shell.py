"""
Module to interact with the shell commands.

:author: xarbulu
:organization: SUSE LLC
:contact: xarbulu@suse.com

:since: 2018-11-15
"""

import logging
import subprocess
import shlex
import re

LOGGER = logging.getLogger('shell')


class ProcessResult:
    """
    Class to store subprocess.Popen output information and offer some
    functionalities

    Args:
        cmd (str): Executed command
        returncode (int): Subprocess return code
        output (str): Subprocess output string
        err (str): Subprocess error string
    """

    def __init__(self, cmd, returncode, output, err):
        self.cmd = cmd
        self.returncode = returncode
        self.output = output.decode() # Make it compatiable with python2 and 3
        self.err = err.decode()


def log_command_results(stdout, stderr):
    """
    Log process stdout and stderr text
    """
    logger = logging.getLogger(__name__)
    if stdout:
        for line in stdout.splitlines():
            logger.info(line)
    if stderr:
        for line in stderr.splitlines():
            logger.error(line)


def find_pattern(pattern, text):
    """
    Find pattern in multiline string

    Args:
        pattern (str): Regular expression pattern
        text (str): string to search in

    Returns:
        Match object if the pattern is found, None otherwise
    """
    for line in text.splitlines():
        found = re.match(pattern, line)
        if found:
            return found
    return None


def format_su_cmd(cmd, user):
    """
    Format the command to be executed by other user using su option

    Args:
        cmd (str): Command to be formatted
        user (str): User to executed the command

    Returns:
        str: Formatted command
    """
    return 'su -lc "{cmd}" {user}'.format(cmd=cmd, user=user)


def execute_cmd(cmd, user=None, password=None):
    """
    Execute a shell command. If user and password are provided it will be
    executed with this user.

    Args:
        cmd (str): Command to be executed
        user (str, opt): User to execute the command
        password (str, opt): User password

    Returns:
        ProcessResult: ProcessResult instance storing subprocess returncode,
            stdout and stderr
    """

    LOGGER.debug('Executing command "%s" with user %s', cmd, user)

    if user is not None:
        cmd = format_su_cmd(cmd, user)
        LOGGER.debug('Command updated to "%s"', cmd)

    proc = subprocess.Popen(
        shlex.split(cmd),
        stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)

    # Make it compatiable with python2 and 3
    if password:
        password = password.encode()
    out, err = proc.communicate(input=password)

    result = ProcessResult(cmd, proc.returncode, out, err)
    log_command_results(out, err)

    return result
