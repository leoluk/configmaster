import codecs
from contextlib import contextmanager
from django.conf import settings
import os
from pipes import quote
import re
from sh import git
from paramiko import SSHException
from scp import SCPException
import shutil
import socket
import tempfile

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential, DeviceType
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException, \
    FirewallRemoteControl
from utils.remote.fortigate import FortigateRemoteControl
from utils.remote.juniper import JuniperRemoteControl


RE_MATCH_FIRST_WORD = re.compile(r'\b\w+\b')


class SSHDeviceHandler(BaseHandler):
    def __init__(self, device):
        """
        A base class for SSH device handlers. Provides self.credential and
        handles the most common OS and Paramiko connection errors. Does not
        provide any connection facilities.

        :type device: configmaster.models.Device
        """

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

        # Handle network/connections errors (all other errors will be caught
        # by the task runner and reported with full traceback).

        except socket.timeout, e:
            self._fail("Client error: Socket timeout")
        except socket.error, e:
            if e.strerror is None:
                # In some cases, a socket error without any message is raised.
                # This would result in an useless, empty error message, so
                # we'll re-raise the exception instead to get a nice traceback.
                raise e
            self._fail("Socket error: %s" % e.strerror)
        except (RemoteException, SSHException), e:
            self._fail("Client error: %s" % str(e))

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(SSHDeviceHandler, self).run_wrapper(*args, **kwargs):
            with self._catch_connection_errors():
                yield


class NetworkDeviceHandler(SSHDeviceHandler):
    RC_CLASSES = {
        u"Fortigate": FortigateRemoteControl,
        u"Juniper": JuniperRemoteControl
    }

    def __init__(self, device):
        """
        A base class for SSH-based network device handlers. Chooses the right
        remote control class, instantiates it as self.connection and
        connects and authenticates with the device using the credential
        from the database.
        """
        super(NetworkDeviceHandler, self).__init__(device)

        self.connection = self._get_fw_remote_control()
        """:type : FirewallRemoteControl"""

    @property
    def _remote_control_class(self):
        """
        Returns the correct remote control class. The device type <->
        class mapping is defined in the FW_RC_CLASSES dictionary.
        """
        try:
            return self.RC_CLASSES[unicode(self.device.device_type.name)]
        except KeyError:
            self._fail("No device controller for device type %s",
                       self.device.device_type)


    def _get_fw_remote_control(self, *args, **kwargs):
        """
        Instantiates and returns the correct remote controller for the
        device's device_type.

        :rtype : FirewallRemoteControl
        """
        return self._remote_control_class(
            self.device.hostname,
            self.device.device_type.connection_setting.ssh_port,
            *args, **kwargs)

    def _connect_ssh(self):
        """
        Does the SSH login and connection setup. This method can be
        overwritten by descendant classes to customize the login behaviour.
        """
        self.connection.connect(self.credential.username,
                                self.credential.password)

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(NetworkDeviceHandler, self).run_wrapper(*args, **kwargs):
            self._connect_ssh()
            yield
            self.connection.close()


class SSHLoginTestHandler(NetworkDeviceHandler):
    pass


class GuessFirewallTypeHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This handler guesses the Firewall type. Right now, it detects
        Juniper SSG firewalls and simply assumes that everything else is a
        Fortigate firewall. The correct device type is assigned to the
        device if it was successfully guessed.

        This task is quite useful if you assign it to a catch-all device type
        for imported firewalls.
        """

        super(GuessFirewallTypeHandler, self).__init__(device)

    @property
    def _remote_control_class(self):
        # Bypass the automatic mapping
        return GuessingFirewallRemoteControl

    def run(self):
        guess = self.connection.guess_type()

        if not guess:
            self._fail("Could not guess Firewall type")
        else:
            device_type = DeviceType.objects.get(name=guess)
            self.device.device_type = device_type
            self.device.save()
            return self._return_success("Guess: %s", guess)


class NetworkDeviceConfigBackupHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This device handler does a config backup for Fortigate and Juniper
        devices and writes the config files to the file system. It can get
        the config using an interactive session or the SCP subsystem,
        if it is supported and enabled for a particular device. It commits
        the config files to a git repository if the
        TASK_FW_CONFIG_DISABLE_GIT setting is enabled.
        """

        super(NetworkDeviceConfigBackupHandler, self).__init__(device)

    def _connect_ssh(self):
        """
        Override the inherited login method and instruct the remote control
        class to not open any SSH channels. Some firewalls (Juniper) only
        support one channel per connection.
        """
        self.connection.connect(self.credential.username,
                                self.credential.password,
                                open_command_channel=False,
                                open_scp_channel=False)

    @staticmethod
    def _git_commit(commit_message):
        """
        Do a git commit in the current directory with the given commit
        message (without adding any changes). Returns True if a commit has
        been made and False if there weren't any changes. Raises an
        exception in case of failure
        """

        # This is, of course, not the most sophisticated approach at
        # interacting with Git but hey, it's simple and it works. Any error
        # code != 0 results in an exception, so there's little risk of
        # silent failure. We should probably replace this with GitPython or
        # any of the full-featured command-line wrappers at some point in
        # the future, but as long as all we're doing is automated commits,
        # it's perfectly fine.

        # Check if there are any staged changes, abort if not (git commit
        # would return an error otherwise).

        if len(git("diff-index", "--name-only", "HEAD", "--")):
            git.commit(message=commit_message)

            # Doing a git push inside the handler means that the entire
            # task would fail if the push fails (for example, if). Doing a
            # push once per run is sufficient, so only push inside the task
            # handler in debug mode.

            if settings.DEBUG:
                git.push()

            changes = True
        else:
            changes = False

        return changes

    def run(self, *args, **kwargs):

        # Create a temporary directory to prevent accidental overwrites,
        # race conditions, and inconsistent state.

        temp_dir = tempfile.mkdtemp()
        destination_file = '{}.txt'.format(self.device.label)
        temp_filename = os.path.join(temp_dir, destination_file)
        filename = os.path.join(
            settings.TASK_CONFIG_BACKUP_PATH,
            RE_MATCH_FIRST_WORD.findall(self.device.group.plural)[0],
            destination_file)

        if not self.device.do_not_use_scp:
            try:
                self.connection.open_scp_channel()
                self.connection.read_config_scp(temp_filename)
            except SCPException, e:
                # For Fortigate devices, the 501-Permission Denied error
                # indicates that the feature is disabled. The remote control
                # has a enable_scp method, which could be used to
                # automatically enable SCP.

                if "501-" in e.args[0]:
                    self._fail("SCP not enabled or permission denied")
                else:
                    raise e
        else:
            self.connection.open_console_channel()
            config = self.connection.read_config()
            with open(temp_filename, 'w') as f:
                f.write(config)

        if (not os.path.exists(temp_filename)
            or not len(open(temp_filename).read(10))):
            self._fail("Config backup failed "
                       "(empty or non-existing backup file)")
        else:

            # Remove all text matched by one of the regular expressions
            # in the device type's config_filter list from the config file.

            if len(self.device.device_type.filter_expressions):

                # The entire file is read into memory, processed,
                # and written back. This is, of course, not particularly
                # memory efficient, but the files we're processing are
                # pretty small (<1MB), so the memory usage is not a concern.
                # This applies to read_config as well, as it keeps the
                # entire file in memory while receiving it. The temporary
                # file is stored in /tmp, which is a tmpfs (in-memory
                # filesystem) on many platforms, so there's no additional
                # disk I/O in these cases.

                with open(temp_filename) as f:
                    raw_config = f.read()

                for regex in self.device.device_type.filter_expressions:
                    raw_config = regex.sub('', raw_config)

                with open(temp_filename, 'w') as f:
                    f.write(raw_config)

            # Juniper SSG firewalls encode their config as ISO-8859-2.
            # Convert it to UTF8 so that all configs use the same encoding.

            if self.device.device_type.name == "Juniper":
                with codecs.open(temp_filename, encoding="iso-8859-2") as f:
                    raw_config = f.read()
                with codecs.open(temp_filename, 'w', encoding="utf8") as f:
                    f.write(raw_config)

            # Move the temporary file to the config folder and clean up
            # the temporary directory.

            if os.path.exists(filename):
                os.unlink(filename)
            os.rename(temp_filename, filename)
            shutil.rmtree(temp_dir)

            # Git operations

            os.chdir(settings.TASK_CONFIG_BACKUP_PATH)

            if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
                return self._return_success("Config backup successful")

            # Commit config changes

            git.add('-u')
            commit_message = u"{} config change on {}{}".format(
                self.device.group, self.device.label,
                u" ({})".format(self.device.name) if self.device.name else "")
            changes = self._git_commit(commit_message)

            # Commit any new, previously untracked configs

            git.add('.')
            commit_message = u"{} config for {} added".format(
                self.device.group, self.device.label)
            changes |= self._git_commit(commit_message)

            return self._return_success("Config backup successful ({})".format(
                "no changes" if not changes else "changes found"
            ))

    @classmethod
    def run_completed(cls):
        super(NetworkDeviceConfigBackupHandler, cls).run_completed()
        os.chdir(settings.TASK_CONFIG_BACKUP_PATH)

        for device_type in DeviceType.objects.all():
            if not device_type.config_filter:
                continue
            filename = os.path.join(
                settings.TASK_CONFIG_BACKUP_PATH, "..",
                'Meta', "{}_filter.txt".format(
                    RE_MATCH_FIRST_WORD.findall(
                        device_type.name.replace(" ", "_"))[0]))

            with codecs.open(filename, 'w', 'utf8') as f:
                f.write("# Automatically generated from database\n\n")
                f.write(device_type.config_filter)

            git.add("--", quote(filename))
            cls._git_commit(
                'Config filter for device type "%s" changed' % device_type.name)

        git.push()

