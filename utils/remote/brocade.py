import paramiko
from utils.remote import common


class BrocadeRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(BrocadeRemoteControl, self).__init__(*args, **kwargs)

    def read_config_scp(self, destination, startup_config=False):
        self.scp.get("startConfig" if startup_config else "runConfig", destination)


