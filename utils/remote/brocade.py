import re

from utils.remote import common

RE_OUTPUT = re.compile(r'(?:\w+@\w+[>#])?(.*)', re.DOTALL)


class BrocadeRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(BrocadeRemoteControl, self).__init__(*args, **kwargs)

        self._date_format = "%H:%M:%S %a %b %d %Y"

    def connect(self, username, password, open_command_channel=True,
                open_scp_channel=False):
        # we want a PTY for shell but not SCP channels
        self.allocate_pty = open_command_channel and not open_scp_channel
        super(BrocadeRemoteControl, self).connect(
            username, password, open_command_channel, open_scp_channel)

    def read_config_scp(self, destination, startup_config=False):
        self.scp.get("startConfig" if startup_config else "runConfig",
                     destination)

    def expect_prompt(self):
        # TODO: does not work in 100% of all cases yet, probably because
        # the prompt is not separated by a newline and confuses pexpect (?)
        # same issue for other devices
        self.interact.expect(r'.*>')

    def run_command(self, command):
        # TODO: workaround for expect_prompt malfunction
        output = super(BrocadeRemoteControl, self).run_command(command)
        return RE_OUTPUT.findall(output)[0]

    def get_raw_time(self):
        time = self.run_command('show clock').strip().split('\n', 1)[-1].split()
        return ' '.join([time[0].split('.', 1)[0].rstrip(',')] + time[2:])


if __name__ == '__main__':
    import getpass

    rc = BrocadeRemoteControl("brocade.continum.net", timeout=5)
    rc.connect("lschabel", getpass.getpass())

    print repr(rc.get_time())
