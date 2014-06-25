from contextlib import contextmanager
from django.conf import settings
import os
from paramiko import SSHException
import socket

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException, FirewallRemoteControl
from utils.remote.fortigate import FortigateRemoteControl
from utils.remote.juniper import JuniperRemoteControl


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
    def run_wrapper(self, *args, **kwargs):
        with super(SSHDeviceHandler, self).run_wrapper(*args, **kwargs):
            with self._catch_connection_errors():
                yield


class FirewallHandler(SSHDeviceHandler):
    FW_RC_CLASSES = {
        u"Fortigate": FortigateRemoteControl,
        u"Juniper": JuniperRemoteControl
    }

    def _get_fw_remote_control_class(self):
        try:
            return self.FW_RC_CLASSES[unicode(self.device.device_type.name)]
        except KeyError, e:
            self._fail("No firewall controller for device type %s", self.device.device_type)


    def _get_fw_remote_control(self):
        """

        :rtype : FirewallRemoteControl
        """
        return self._get_fw_remote_control_class()(
            self.device.hostname,
            self.device.device_type.connection_setting.ssh_port)

    def __init__(self, device):
        super(FirewallHandler, self).__init__(device)
        """:type : FirewallRemoteControl"""
        self.connection = self._get_fw_remote_control()


    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(FirewallHandler, self).run_wrapper(*args, **kwargs):
            self.connection.connect(self.credential.username, self.credential.password)
            yield
            self.connection.close()


class GuessFirewallTypeHandler(FirewallHandler):
    def _get_fw_remote_control_class(self):
        return GuessingFirewallRemoteControl

    def run(self):
        guess = self.connection.guess_type()

        if not guess:
            self._fail("Could not guess Firewall type")
        else:
            return self._return_success("Guess: %s", guess)


class FirewallConfigBackupHandler(FirewallHandler):
    def run(self, *args, **kwargs):
        config = self.connection.read_config()

        filename = os.path.join(settings.TASK_FW_CONFIG_PATH, '{}.txt'.format(self.device.label))

        if config:
            with open(filename, 'w') as f:
                f.write(config)
                return self._return_success("Configuration successfully backed up")
        else:
            self._fail("Empty configuration file read from firewall")
