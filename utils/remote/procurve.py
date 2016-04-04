from utils.contrib import vt100
from utils.remote import common


class ProCurveRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(ProCurveRemoteControl, self).__init__(*args, **kwargs)
        self._skipped_banner = False
        self._date_format = "%a %b %d %H:%M:%S %Y"

    def connect(self, username, password, open_command_channel=True,
                open_scp_channel=False):
        # ProCurve switches close the channel if a shell without TTY is
        # requested.
        self.allocate_pty = open_command_channel and not open_scp_channel

        super(ProCurveRemoteControl, self).connect(username, password,
                                                   open_command_channel,
                                                   open_scp_channel)

    def read_config_scp(self, destination, startup_config=False):
        self.scp.get(
            "cfg/startup-config" if startup_config else "cfg/running-config",
            destination)

    @staticmethod
    def _parse_term_output(output):
        term = vt100.Terminal(verbosity=-1)
        term.parse(output)
        return '\n'.join(term.to_string().strip().split('\n')[2:])

    def _skip_banner(self):
        self.interact.expect(".*Press any key to continue.*")
        self.interact.send('\n')

    def run_command(self, command):
        if not self._skipped_banner:
            self._skip_banner()
            self._skipped_banner = True
        output = super(ProCurveRemoteControl, self).run_command(command)
        return self._parse_term_output(output)

    def expect_prompt(self):
        self.interact.expect(r'.*#.*$')

    def get_raw_time(self):
        return self.run_command('show time')

if __name__ == '__main__':
    import getpass

    rc = ProCurveRemoteControl("procurve.continum.net")
    rc.connect(common.DEBUG_USER, getpass.getpass())

    time = rc.get_time()

    print repr(time)