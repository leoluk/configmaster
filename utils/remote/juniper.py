from utils.remote.common import OperationalError

__author__ = 'lschabel'

import re

import common

# FIXME: Regex appears to be quite slow
RE_SYSINFO = re.compile(
    r""".*^Product Name:\s+(?P<model>.+)$
.*^Serial Number:\s+(?P<serial>\d+).*$
.*^Hardware Version:\s+(?P<hwrev>[^\s,]+).*$
.*^Software Version:\s+(?P<swrev>[^\s,]+).*$""", re.DOTALL | re.MULTILINE)


class JuniperRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(JuniperRemoteControl, self).__init__(*args, **kwargs)

    def change_admin_password(self, new_password, verify=True):
        # TODO: verify that login user is admin user ("get admin name")

        self.run_command('set admin password "%s"' % common.sanitize(new_password))
        self.save_and_apply()

        if verify:
            if not self.verify_login(self.username, new_password):
                raise OperationalError("Password change failed")
            else:
                return True

    def add_admin(self, username, password, privilege="read-only",
                  role=None, sshkey=None, ssh_only_key=False, verify=True):

        self.run_command('set admin user "%s" password "%s" privilege "%s"' % (
            common.sanitize(username),
            common.sanitize(password),
            common.sanitize(privilege)))

        if role:
            self.run_command('set admin user "%s" role "%s"' % (
                common.sanitize(username),
                common.sanitize(role)))

        if sshkey:
            self.run_command('set ssh pka-dsa user-name "%s" key "%s"' % (
                common.sanitize(username),
                common.sanitize(sshkey)))

            if ssh_only_key:
                self.run_command('set admin scs password disable username "%s"' % (
                    common.sanitize(username)))

        if verify:
            if sshkey and ssh_only_key:
                raise NotImplementedError("Verification not supported for passwordless SSH login")

            if not self.verify_login(username, password):
                raise OperationalError("Failed to add new admin user")
            else:
                return True

        self.save_and_apply()

    def enable_scp(self):
        self.run_command("set scp enable")
        self.save_and_apply()

    def connect(self, username, password, **kwargs):
        super(JuniperRemoteControl, self).connect(username, password, **kwargs)

        if self.chan:
            self.expect_prompt()

    def run_command(self, command):
        self.interact.send(command)
        self.expect_prompt()

        if "^--" in self.interact.current_output_clean:
            raise common.OperationalError("Command '%s' failed: %s" % (
                command, self.interact.current_output_clean
            ))
        else:
            return self.interact.current_output_clean

    def save_and_apply(self):
        self.run_command("save")

    def read_config_scp(self, destination, startup_config=False):
        if startup_config:
            raise NotImplementedError("Juniper SSG does not support"
                                      "startup config copy over SCP")
        self.scp.get("ns_sys_config", destination)

    def read_config(self, startup_config=False):
        with self.ctx_term_setup():
            self.run_command("get config" +
                             (" saved"  if startup_config else ""))
            return self.interact.current_output_clean.strip("ssg5-serial->").strip()

    def read_sysinfo(self):
        with self.ctx_term_setup():
            output = self.run_command("get system")
            match = RE_SYSINFO.match(output)

            if match:
                return match.groupdict()

    def expect_prompt(self):
        self.interact.expect(r'.*->.*')

    def setup_terminal(self):
        self.run_command("set console page 0")
        self.run_command("set console timeout 0")

    def teardown_terminal(self):
        # TODO: is 10 the default value for page?
        self.run_command("set console page 10")
        self.run_command("set console timeout 10")

    def close(self):
        if self.chan:
            self.interact.send("exit")
        super(JuniperRemoteControl, self).close()


if __name__ == '__main__':
    import getpass

    rc = JuniperRemoteControl("192.168.50.50", port=2222, timeout=1)
    rc.connect("root", getpass.getpass())
    rc.change_admin_password(getpass.getpass())