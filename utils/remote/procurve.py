from utils.remote import common


class ProCurveRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(ProCurveRemoteControl, self).__init__(*args, **kwargs)

    def connect(self, username, password, open_command_channel=True,
                open_scp_channel=False):
        # ProCurve switches close the channel if a shell without TTY is
        # requested.
        self.allocate_pty = False

        super(ProCurveRemoteControl, self).connect(username, password,
                                                   open_command_channel,
                                                   open_scp_channel)


    def read_config_scp(self, destination, startup_config=False):
        self.scp.get(
            "cfg/startup-config" if startup_config else "cfg/running-config",
            destination)


