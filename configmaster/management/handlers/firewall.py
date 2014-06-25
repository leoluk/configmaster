from contextlib import contextmanager
from paramiko import SSHException
import socket
from decorator import decorator

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException
from utils.remote.fortigate import FortigateRemoteControl
from utils.remote.juniper import JuniperRemoteControl



# All run() methods of base classes are context managers. This allows
# the base class to catch exceptions raised in the child class.
# This decorator calls the super method as context manager and should
# be used to wrap the run() methods of the actual handler classes.
# This eliminates the need to define a custom method like _run_ssh and
# _run_ssh_firewall, but is a bit more complicated. The alternative
# would be to insert an intermediate layer between the task runner
# and the handler which catches the exceptions (this way, the run()
# method would only be implemented in the actual handler). I've not
# yet decided which approach is better.

@decorator
def parent_context(f, *args, **kwargs):
    with getattr(super(type(args[0]), args[0]), f.func_name)():
        return f(*args, **kwargs)


class SSHDeviceHandler(BaseHandler):
    def __init__(self, device):
        super(SSHDeviceHandler, self).__init__(device)

        if self.device.credential:
            self.credential = self.device.credential
        else:
            self.credential = self.device.device_type.credential
        if not self.device.device_type.connection_setting:
            self._fail("No connection setting for device")
        elif not self.device.device_type.connection_setting.ssh_port:
            self._fail("Invalid SSH port setting")

        if not self.credential or self.credential.type != Credential.TYPE_PLAINTEXT:
            self._fail("No valid credential for device")

    @contextmanager
    def _catch_connection_errors(self):
        try:
            yield

        # Handle network/connections errors (all other errors will be caught by the task
        # runner and reported with full traceback).

        except socket.error, e:
            self._fail("Socket error: %s" % e.strerror)
        except (RemoteException, SSHException), e:
            self._fail("Client error: %s" % str(e))

    @contextmanager
    def run(self, *args, **kwargs):
        with self._catch_connection_errors():
            yield


class FirewallHandler(SSHDeviceHandler):
    FW_RC_CLASSES = {
        "Fortigate": FortigateRemoteControl,
        "Juniper": JuniperRemoteControl
    }

    def _get_fw_remote_control(self):
        """
        :rtype : common.FirewallRemoteControl
        """
        try:
            return self.FW_RC_CLASSES[self.device.device_type]
        except KeyError:
            self._fail("No firewall controller for device type %s", self.device.device_type)

    def __init__(self, device):
        super(FirewallHandler, self).__init__(device)
        self.connection = self._get_fw_remote_control()


class GuessFirewallTypeHandler(SSHDeviceHandler):
    @parent_context
    def run(self):
        guesser = GuessingFirewallRemoteControl(self.device.hostname,
                                                self.device.device_type.connection_setting.ssh_port)
        guesser.connect(self.credential.username, self.credential.password)
        guess = guesser.guess_type()

        if not guess:
            self._fail("Could not guess Firewall type")
        else:
            return self._return_success("Guess: %s", guess)

        guesser.close()
