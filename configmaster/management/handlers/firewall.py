from paramiko import SSHException
import socket

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException


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

    def _ssh_run(self):
        raise NotImplementedError("SSHDeviceHandler is a base class and not supposed to be run directly.")

    def run(self, *args, **kwargs):
        try:
            return self._ssh_run()

        # Handle network/connections errors (all other errors will be caught by the task
        # runner and reported with full traceback).

        except socket.error, e:
            self._fail("Socket error: %s" % e.strerror)
        except (RemoteException, SSHException), e:
            self._fail("Client error: %s" % str(e))


class ConnectedFirewallHandler(SSHDeviceHandler):
    def _ssh_run(self):
        return super(ConnectedFirewallHandler, self)._ssh_run()


class GuessFirewallTypeHandler(SSHDeviceHandler):
    def _ssh_run(self):
        guesser = GuessingFirewallRemoteControl(self.device.hostname,
                                                self.device.device_type.connection_setting.ssh_port)
        guesser.connect(self.credential.username, self.credential.password)
        guess = guesser.guess_type()

        if not guess:
            self._fail("Could not guess Firewall type")
        else:
            return self._return_success("Guess: %s", guess)

        guesser.close()

