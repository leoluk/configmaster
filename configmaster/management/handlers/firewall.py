from contextlib import contextmanager
from django.conf import settings
import os
from sh import git
from paramiko import SSHException
from scp import SCPException
import socket
import tempfile

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


    def _get_fw_remote_control(self, *args, **kwargs):
        """

        :rtype : FirewallRemoteControl
        """
        return self._get_fw_remote_control_class()(
            self.device.hostname,
            self.device.device_type.connection_setting.ssh_port,
            *args, **kwargs)

    def __init__(self, device):
        super(FirewallHandler, self).__init__(device)
        """:type : FirewallRemoteControl"""
        self.connection = self._get_fw_remote_control()


    def _connect_ssh(self):
        self.connection.connect(self.credential.username, self.credential.password)

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(FirewallHandler, self).run_wrapper(*args, **kwargs):
            self._connect_ssh()
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
    def _connect_ssh(self):
        self.connection.connect(self.credential.username, self.credential.password,
                                open_command_channel=False, open_scp_channel=True)

    @staticmethod
    def _git_commit(commit_message):
        if len(git("diff-index", "--name-only", "HEAD", "--")):
            git.commit(message=commit_message)
            if settings.DEBUG:
                git.push()
            changes = True
        else:
            changes = False
        return changes

    def run(self, *args, **kwargs):
        temp_dir = tempfile.mkdtemp()
        destination_file = '{}.txt'.format(self.device.label)
        temp_filename = os.path.join(temp_dir, destination_file)
        filename = os.path.join(settings.TASK_FW_CONFIG_PATH, destination_file)

        if not self.device.do_not_use_scp:
            try:
                self.connection.read_config_scp(temp_filename)
            except SCPException, e:
                if "501-" in e.args[0]:
                    self.device.do_not_use_scp = True
                    self.device.save()
                    self._fail("SCP not enabled or permission denied, retrying without SCP on next run")
                else:
                    raise e
        else:
            config = self.connection.read_config()
            with open(temp_filename, 'w') as f:
                f.write(config)

        if not os.path.exists(temp_filename) or not len(open(temp_filename).read(10)):
            self._fail("Config backup failed (empty or non-existing backup file)")
        else:
            if os.path.exists(filename):
                os.unlink(filename)
            os.rename(temp_filename, filename)

            os.chdir(settings.TASK_FW_CONFIG_PATH)

            # Commit config changes
            git.add('-u')
            commit_message = "Firewall config change on %s" % self.device.label
            changes = self._git_commit(commit_message)

            # Commit any new, previously untracked configs
            git.add('.')
            commit_message = "Firewall config for %s added" % self.device.label
            changes |= self._git_commit(commit_message)

            return self._return_success("Config backup successful ({})".format(
                "no changes" if not changes else "changes found"
            ))

