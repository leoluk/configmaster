from contextlib import contextmanager
import scp
import socket
import paramiko
from subprocess import list2cmdline

from utils import pexpect


__author__ = 'lschabel'


def sanitize(value):
    return list2cmdline([value])


class RemoteException(RuntimeError):
    pass


class ConnectionError(RemoteException):
    pass


class OperationalError(RemoteException):
    pass


class LoginFailedException(RemoteException):
    pass


class BaseRemoteControl(object):
    def __init__(self, hostname):
        self.hostname = hostname


# TODO: verbose logging

class SSHRemoteControl(BaseRemoteControl):
    def __init__(self, hostname, port=22, hostkey=None, timeout=3, cmd_timeout=10):
        super(SSHRemoteControl, self).__init__(hostname)

        self.transport = None
        self.port = port
        self.hostkey = hostkey
        self.chan = None
        self.username = None
        self.password = None
        self.timeout = timeout
        self.interact = None
        self.scp = None
        self.cmd_timeout = cmd_timeout
        self.allocate_pty = True

    def _connect_transport(self, transport, username=None, password=None):

        if not username:
            username = self.username
        if not password:
            password = self.password

        try:
            transport.start_client()
        except paramiko.SSHException:
            raise ConnectionError("SSH negotiation failed")

        # TODO: verify host key here

        try:
            transport.auth_password(username, password)

            # double check, auth_password should already raise the exception
            if not transport.is_authenticated():
                raise paramiko.AuthenticationException()

        except paramiko.AuthenticationException:
            raise LoginFailedException("SSH login failed for user %s" % username)

    def _make_transport(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.timeout:
                sock.settimeout(self.timeout)
            sock.connect((self.hostname, self.port))
            return paramiko.Transport(sock)
        except (paramiko.SSHException, socket.timeout), e:
            raise ConnectionError("SSH socket failed: %s" % str(e))

    def _open_console_channel(self):
        self.chan = self.transport.open_session()
        self.chan.settimeout(self.timeout)
        if self.allocate_pty:
            self.chan.get_pty()
        self.chan.invoke_shell()
        self.interact = pexpect.SSHClientInteraction(self.chan, timeout=self.cmd_timeout)

    def _open_scp_channel(self):
        self.scp = scp.SCPClient(self.transport)

    def connect(self, username, password, open_command_channel=True,
                open_scp_channel=False):
        self.username = username
        self.password = password

        self.transport = self._make_transport()
        self._connect_transport(self.transport)

        # Note: opening multiple channels is not supported by many embedded devices!

        if open_command_channel:
            self._open_console_channel()
        if open_scp_channel:
            self._open_scp_channel()


    def close(self):
        if self.chan:
            self.chan.close()
        if self.transport:
            self.transport.close()

    def verify_login(self, username, password):
        transport = None

        try:
            transport = self._make_transport()
            self._connect_transport(transport, username, password)
        except LoginFailedException:
            return False
        else:
            return transport.is_authenticated()
        finally:
            if transport:
                transport.close()


class FirewallRemoteControl(SSHRemoteControl):
    def __init__(self, hostname, port=22, hostkey=None, timeout=5, cmd_timeout=10):
        super(FirewallRemoteControl, self).__init__(hostname, port, hostkey, timeout, cmd_timeout)
        self.allocate_pty = False

    def change_admin_password(self, new_password, verify=True):
        raise NotImplementedError

    def add_admin(self, username, password, privilege="read-only",
                  role=None, sshkey=None, ssh_only_key=False, verify=True):
        raise NotImplementedError

    def enable_scp(self):
        raise NotImplementedError

    def save_and_apply(self):
        raise NotImplementedError

    def expect_prompt(self):
        raise NotImplementedError

    def read_config(self):
        raise NotImplementedError

    def read_config_scp(self, destination):
        raise NotImplementedError

    def setup_terminal(self):
        raise NotImplementedError

    def teardown_terminal(self):
        raise NotImplementedError

    def run_command(self, command):
        self.interact.send(command)
        self.expect_prompt()
        return self.interact.current_output_clean

    @contextmanager
    def ctx_term_setup(self):
        try:
            self.setup_terminal()
            yield
        finally:
            self.teardown_terminal()


class GuessingFirewallRemoteControl(FirewallRemoteControl):
    def guess_type(self):
        prompt = self.chan.recv(1024)

        if "Remote Management Console" in prompt:
            return "Juniper"
        elif "#" in prompt:
            # if it's not a Juniper, simply assume it's a Fortigate firewall
            return "Fortigate"


if __name__ == '__main__':
    import getpass

    rc = GuessingFirewallRemoteControl("192.168.50.50")
    rc.connect("root", getpass.getpass())
    print rc.guess_type()