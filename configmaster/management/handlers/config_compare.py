import sh
import shutil
import os
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler


class NetworkDeviceCompareWithStartupHandler(
    NetworkDeviceConfigBackupHandler):

    def run(self, *args, **kwargs):
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

            if running_config != startup_config:
                self._fail("Running config differs from startup config")
            else:
                return self._return_success("Running config equals "
                                            "startup config")

        finally:
            pass
            #shutil.rmtree(temp_dir)
