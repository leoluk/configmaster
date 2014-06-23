from paramiko import SSHException
import socket

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException


class FirewallHandler(BaseHandler):
    def run(self, *args, **kwargs):
        return super(FirewallHandler, self).run(*args, **kwargs)


class GuessFirewallType(FirewallHandler):
    def run(self, commons=None, *args, **kwargs):
        super(GuessFirewallType, self).run(*args, **kwargs)
        device = self.device

        if device.credential:
            credential = self.device.credential
        else:
            credential = self.device.device_type.credential

        if not device.device_type.connection_setting:
            self._fail("No connection setting for device")
        elif not device.device_type.connection_setting.ssh_port:
            self._fail("Invalid SSH port setting")

        # Key-based login not yet supported
        if not credential or credential.type != Credential.TYPE_PLAINTEXT:
            self._fail("No valid credential for device")

        try:
            guesser = GuessingFirewallRemoteControl(device.hostname, device.device_type.connection_setting.ssh_port)
            guesser.connect(credential.username, credential.password)
            guess = guesser.guess_type()

            if not guess:
                self._fail("Could not guess Firewall type")
            else:
                return self._return_success("Guess: %s", guess)

            guesser.close()

        # Handle network/connections errors (all other errors will be caught by the task
        # runner and reported with full traceback).

        except socket.error, e:
            self._fail("Socket error: %s" % e.strerror)
        except (RemoteException, SSHException), e:
            self._fail("Client error: %s" % str(e))
