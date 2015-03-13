import sh
import re
import shutil
import os
import difflib
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler


RE_IGNORE_CONSOLE = re.compile(r"set console page \d+\s")


class NetworkDeviceCompareWithStartupHandler(
    NetworkDeviceConfigBackupHandler):

    def _compare_config(self, startup_config, running_config):
        if startup_config == running_config:
            return self._return_success("Running config equals startup config")
        else:
            self._fail_long_message(
                "Running/startup config differ (see report)",
                '\n'.join(difflib.unified_diff(startup_config.splitlines(),
                                               running_config.splitlines())))

    def alternative_config_compare(self):
        self.connection.open_console_channel()
        self.connection.expect_prompt()
        self.connection.setup_terminal()
        self.connection.terminal_setup = True
        sysinfo = self.connection.read_sysinfo()
        self.device.version_info = "{model} - {swrev}".format(**sysinfo)
        self.device.save()

        running_config = self.connection.read_config(startup_config=False)
        startup_config = self.connection.read_config(startup_config=True)

        self.connection.teardown_terminal()

        # TODO: this is Juniper SSG specific and should probably be moved
        # to juniper.py

        startup_config = RE_IGNORE_CONSOLE.sub("", startup_config.split('\n', 5)[-1])
        running_config = RE_IGNORE_CONSOLE.sub("", running_config.split('\n', 1)[1])

        return self._compare_config(startup_config, running_config)


    def run(self, *args, **kwargs):
        if self.device.device_type.alternative_config_compare:
            return self.alternative_config_compare()

        filename, temp_dir, temp_filename = self._initialize_temporary_directory()
        self._read_config_from_device(temp_filename, startup_config=True)
        self._cleanup_config(temp_filename)

        try:
            if not os.path.exists(filename):
                self._fail("Nothing to compare to (no config backup found)")

            with open(filename) as f:
                running_config = f.read()
            with open(temp_filename) as f:
                startup_config = f.read()

            return self._compare_config(startup_config, running_config)

        finally:
            shutil.rmtree(temp_dir)
