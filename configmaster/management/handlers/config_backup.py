#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import codecs
from django.conf import settings
import os
from pipes import quote
from scp import SCPException
import shutil
import tempfile
from sh import git, find

from configmaster.management.handlers.network_device import \
    NetworkDeviceHandler, RE_MATCH_FIRST_WORD
from configmaster.models import DeviceType, DeviceGroup, Repository, Device



class NetworkDeviceConfigBackupHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This device handler does a config backup for network devices and
        writes the config files to the file system. It can get the config
        using an interactive session or the SCP subsystem, if it is
        supported and enabled for a particular device. It commits the config
        files to a git repository if the
        :option:`TASK_CONFIG_BACKUP_DISABLE_GIT` setting is set.

        All SSH connection logic is inherited from its parent class.

        In most cases, implementing a new device type should not necessitate
        subclassing.
        """

        super(NetworkDeviceConfigBackupHandler, self).__init__(device)

    def _connect_ssh(self):
        """
        Overrides the inherited login method and instructs the remote control
        class to not open any SSH channels by default. Some devices (Juniper
        SSG!) only support one channel per connection.
        """
        self.connection.connect(
            self.credential.username,
            self.credential.password,
            open_command_channel=False,
            open_scp_channel=False)

    @staticmethod
    def _git_commit(commit_message):
        """
        Do a git commit in the current directory with the given commit
        message (without adding any changes). Instead of using a Git wrapper
        library, we directly call the Git binaries using :mod:`sh`, which
        ensures that error return codes are either handled or raised.

        If the :option:`DEBUG` setting is set, a Git push is attempted after
        commiting.

        Args:
            commit_message (str): Single-line commit message

        Returns:
            *True* if a commit has been made and `False` if there weren't any
            changes.

        Raises:
            :exc:`sh.ErrorReturnCode` exception in case of failure.

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

            # Doing a git push inside the handler means that the entire task
            # would fail if the push fails. Doing a push once per run is
            # sufficient, so only push inside the task handler in debug mode.

            if settings.DEBUG:
                git.push()

            changes = True
        else:
            changes = False

        return changes

    def _get_config_checksum(self):
        """
        Read the config checksum from the device using a separate SSH
        connection. Only supported on certain devices.

        Raises:
            NotImplementedError: if device does not support checksumming

        """

        # Open a separate connection to the device, bypassing the parent's
        # connection initializer. This means that we have to handle the
        # entire connection life cycle manually!

        connection = self._get_fw_remote_control()
        """:type : NetworkDeviceRemoteControl"""

        try:
            connection.connect(self.credential.username, self.credential.password)
            return connection.get_config_checksum()
        finally:
            connection.close()

    def _compare_config_checksum(self):
        """
        Returns True if the config checksum is identical. Updates the
        :attr:`configmaster.models.Device.last_checksum` field if necessary.
        """

        self.checksum = self._get_config_checksum()

        if self.checksum != self.device.last_checksum:
            return False
        else:
            return True

    def _read_config_from_device(
            self, temp_filename, startup_config=False, use_scp=True):
        """
        This method implements the actual configuration backup part. It
        reads the config from the device (either interactively or by using
        SCP) and writes it to a file.

        Called from the main config backup method (:meth:`run`).

        Args:
            temp_filename (str): Path to write config file to

            startup_config (bool): Reads the startup config if `True` or the
                running config if `False`.

            use_scp (bool): Read the config using SCP (``read_config_scp``
                instead of ``read_config``).

        """
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
        """
        Create a device-specific temporary directory and a temporary filename.

        A temporary file is necessary for the config backup in order to
        prevent accidental overwrites, race conditions, and inconsistent state.

        Called from the main config backup method (:meth:`run`).

        Returns:
            tuple: (filename, temp_dir, temp_filename)

        """

        temp_dir = tempfile.mkdtemp()
        filename = self.device.config_backup_filename
        temp_filename = os.path.join(temp_dir, os.path.basename(filename))

        if not os.path.exists(os.path.dirname(filename)):
            os.mkdir(os.path.dirname(filename))

        return filename, temp_dir, temp_filename

    def _cleanup_and_convert_config(self, temp_filename):
        """
        Applies the devices type's regex filters to the temporary file.

        If the device type is named ``Juniper SSG``, the file is converted
        from ISO-8859-2 encoding to UTF-8.

        Called from the main config backup method (:meth:`run`).
        """

        # The entire file is read into memory, processed,
        # and written back. This is, of course, not particularly
        # memory efficient, but the files we're processing are
        # pretty small (<1MB), so the memory usage is not a concern.
        # This applies to read_config as well, as it keeps the
        # entire file in memory while receiving it. The temporary
        # file is stored in /tmp, which is a tmpfs (in-memory
        # filesystem) on many platforms, so there's no additional
        # disk I/O in these cases (and it would be in the page cache
        # either way).

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
        #
        # TODO: remove hardcoded device type name (should be a type flag)
        #
        if self.device.device_type.name == "Juniper SSG":
            with codecs.open(temp_filename, encoding="iso-8859-2") as f:
                raw_config = f.read()
            with codecs.open(temp_filename, 'w', encoding="utf8") as f:
                f.write(raw_config)

    def _return_success(self, message, *args):
        has_new_checksum = getattr(self, 'checksum', False)
        if has_new_checksum and self.device.last_checksum != self.checksum:
                self.device.last_checksum = self.checksum
                self.device.save(update_fields=['last_checksum'])
        return super(
            NetworkDeviceConfigBackupHandler, self
        )._return_success(message, *args)

    def run(self, *args, **kwargs):
        """
        Per-device config backup. Calls all of the methods above. The device
        config is stored in the repository, committed and the version info
        is extracted and saved.

        Acquires a global lock on the repository. The task runner already
        holds the device lock.

        If the device checksum did not change, the whole process is skipped.

        .. todo:: Document checksum mechanism
        """

        if self.device.device_type.checksum_config_compare:
            if self._compare_config_checksum():
                return self._return_success(
                    "Config backup successful (skipped, checksum identical)")

        filename, temp_dir, temp_filename = (
            self._initialize_temporary_directory())

        self._read_config_from_device(temp_filename)
        self._cleanup_and_convert_config(temp_filename)

        # Move the temporary file to the config folder and clean up
        # the temporary directory.

        self.device.group.repository.lock.acquire()

        try:
            if os.path.exists(filename):
                os.unlink(filename)
            shutil.move(temp_filename, filename)
        finally:
            shutil.rmtree(temp_dir)

        # Git operations

        os.chdir(self.device.group.repository.path)

        if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
            return self._return_success("Config backup successful")

        # Commit config changes

        git.add('-u')
        commit_message = u"{} config change on {} ({})".format(
            self.device.group, self.device.label, self.device)
        changes = self._git_commit(commit_message)

        # Commit any new, previously untracked configs

        git.add('.')
        commit_message = u"{} config for {} added".format(
            self.device.group, self.device.label)
        changes |= self._git_commit(commit_message)

        self.device.group.repository.lock.release()

        # Extract version info

        if self.device.device_type.version_regex and changes:
            self.device.version_info = self.device._version_info

        return self._return_success("Config backup successful ({})".format(
            "no changes" if not changes else "changes found"
        ))

    def cleanup(self):
        """
        Does a ``git reset --hard`` to clean up any left-over temporary
        files in the repository.
        """
        if self.device.group.repository.lock.acquired:
            os.chdir(self.device.group.repository.path)
            git.reset('--hard')

    @classmethod
    def run_completed(cls):
        """
        Many things happen once run is complete. At this point, all of the
        device configs are already committed.

        * Each device is symlinked in the `ByHostname` directory and symlinks
          for deleted device are removed.

        * All repositories are pushed to the default remote.

        * All device type regex filters are committed to the repository
          with the ID 1. This is done in order to track changes to the filters.

        """

        super(NetworkDeviceConfigBackupHandler, cls).run_completed()

        # Generate "ByHostname" symlinks

        for repository in Repository.objects.all():
            repository.lock.acquire()

        for device in Device.objects.all():
            if device.group.repository:
                symlink_dir = os.path.join(
                    device.group.repository.path, "_ByHostname")
                if not os.path.exists(symlink_dir):
                    os.mkdir(symlink_dir)
                symlink = os.path.join(symlink_dir, '{}.txt'.format(
                    device.hostname))
                if not os.path.islink(symlink) and os.path.exists(
                        device.config_backup_filename):
                    os.symlink(os.path.relpath(
                        device.config_backup_filename, symlink_dir), symlink)

        # Git push and config filter commits

        if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
            for repository in Repository.objects.all():
                repository.lock.release()
            return

        for repository in Repository.objects.all():
            os.chdir(repository.path)
            # Clean up broken symlinks
            find('-L', '_ByHostname', '-type', 'l', '-delete')
            git.add('-A', '_ByHostname')
            if cls._git_commit('Symlink updates'):
                git.push()

        for device_group in DeviceGroup.objects.all():
            if device_group.repository:
                os.chdir(device_group.repository.path)
                git.push()

        # TODO: make the repository ID configurable

        os.chdir(Repository.objects.get(id=1).path)

        for device_type in DeviceType.objects.all():
            if not device_type.config_filter:
                continue
            filename = os.path.join(
                Repository.objects.get(id=1).path,
                'Meta', "{}_filter.txt".format(
                    RE_MATCH_FIRST_WORD.findall(
                        device_type.name.replace(" ", "_"))[0]))

            with codecs.open(filename, 'w', 'utf8') as f:
                f.write("# Automatically generated from database\n\n")
                f.write(device_type.config_filter)

            git.add("--", quote(filename))
            if cls._git_commit('Config filter for device type "%s" changed' % device_type.name):
                git.push()

        for repository in Repository.objects.all():
            repository.lock.release()
