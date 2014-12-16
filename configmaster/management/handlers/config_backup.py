import codecs
from django.conf import settings
import os
from pipes import quote
from scp import SCPException
import shutil
import tempfile
from sh import git

from configmaster.management.handlers.network_device import \
    NetworkDeviceHandler, RE_MATCH_FIRST_WORD
from configmaster.models import DeviceType, DeviceGroup


__author__ = 'lschabel'


class NetworkDeviceConfigBackupHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This device handler does a config backup for network devices and
        writes the config files to the file system. It can get the config
        using an interactive session or the SCP subsystem, if it is
        supported and enabled for a particular device. It commits the config
        files to a git repository if the TASK_FW_CONFIG_DISABLE_GIT setting
        is enabled.
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

    def _read_config_from_device(self, temp_filename, startup_config=False,
                                 use_scp=True):
        if not self.device.do_not_use_scp and use_scp:
            try:
                self.connection.open_scp_channel()
                self.connection.read_config_scp(temp_filename, startup_config)
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
            config = self.connection.read_config(startup_config)
            with open(temp_filename, 'w') as f:
                f.write(config)

        if (not os.path.exists(temp_filename)
            or not len(open(temp_filename).read(10))):
            self._fail("Config backup failed "
                       "(empty or non-existing backup file)")

    def _initialize_temporary_directory(self):

        # Create a temporary directory to prevent accidental overwrites,
        # race conditions, and inconsistent state.

        temp_dir = tempfile.mkdtemp()
        destination_file = '{}.txt'.format(self.device.label)
        temp_filename = os.path.join(temp_dir, destination_file)
        filename = os.path.join(
            self.device.group.repository.path,
            RE_MATCH_FIRST_WORD.findall(
                self.device.group.plural.replace(' ', ''))[0],
            destination_file)

        if not os.path.exists(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))

        return filename, temp_dir, temp_filename

    def _cleanup_config(self, temp_filename):

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

        # Remove all text matched by one of the regular expressions
        # in the device type's config_filter list from the config file.

        if len(self.device.device_type.filter_expressions):
            for regex in self.device.device_type.filter_expressions:
                raw_config = regex.sub('', raw_config)

        with open(temp_filename, 'w') as f:
            f.write(raw_config.strip('\x00'))

        # Juniper SSG firewalls encode their config as ISO-8859-2.
        # Convert it to UTF8 so that all configs use the same encoding.
        if self.device.device_type.name == "Juniper SSG":
            with codecs.open(temp_filename, encoding="iso-8859-2") as f:
                raw_config = f.read()
            with codecs.open(temp_filename, 'w', encoding="utf8") as f:
                f.write(raw_config)

    def run(self, *args, **kwargs):

        filename, temp_dir, temp_filename = self._initialize_temporary_directory()
        self._read_config_from_device(temp_filename)

        self._cleanup_config(temp_filename)

        # Move the temporary file to the config folder and clean up
        # the temporary directory.

        if os.path.exists(filename):
            os.unlink(filename)
        os.rename(temp_filename, filename)
        shutil.rmtree(temp_dir)

        # Git operations

        os.chdir(self.device.group.repository.path)

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

        for device_group in DeviceGroup.objects.all():
            os.chdir(device_group.repository.path)

            if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
                return

            for device_type in DeviceType.objects.all():
                if not device_type.config_filter:
                    continue
                filename = os.path.join(
                    settings.TASK_CONFIG_BACKUP_PATH,
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