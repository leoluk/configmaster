from contextlib import contextmanager
import re
import cStringIO

import common

__author__ = 'lschabel'

RE_SYSINFO = re.compile(r""".*^.*?Version:\s+(?P<model>.+?)\s(?P<swrev>.+?)$.*
^Serial-Number:\s+(?P<serial>FG.+?)$""", re.DOTALL | re.MULTILINE)


class FortigateRemoteControl(common.FirewallRemoteControl):
    def __init__(self, *args, **kwargs):
        super(FortigateRemoteControl, self).__init__(*args, **kwargs)

    def expect_prompt(self, in_block=False):
        if in_block:
            self.interact.expect(r'.+\(.+\)\s*[#$].*')
        else:
            self.interact.expect(r'.+\s+[#$].*')

    def run_command(self, command, in_block=False):
        self.interact.send(command)
        self.expect_prompt(in_block=in_block)

        if "Command fail" in self.interact.current_output_clean:
            raise common.OperationalError("Command '%s' failed: %s" % (
                # TODO: strip prompt
                command, self.interact.current_output_clean
            ))
        else:
            return self.interact.current_output_clean

    def change_admin_password(self, new_password, username=None, verify=True):
        if not username:
            username = self.username

        with self.ctx_config_block("system admin"):
            with self.ctx_edit_block(common.sanitize(username)):
                self.run_command("set password %s" % common.sanitize(new_password), True)

        if verify:
            if not self.verify_login(username, new_password):
                raise common.OperationalError("Password change failed")
            else:
                return True

    def read_config(self):
        """
        Read the config from a Fortigate firewall using a SSH console
        session and direct command execution. This eliminates the need to
        disable the pager (but its output is still included and has to be
        removed).

        This feature is deprecated for Fortigate devices, as it has multiple
        issues (see T124 and T52) and is no longer necessary (SCP config
        backup available on all devices).
        """

        # TODO: extract exec_command boilerplate into generic method
        chan = self.transport.open_session()
        chan.settimeout(self.timeout)
        output_file = chan.makefile()
        chan.exec_command("show")
        output = output_file.read()
        chan.close()
        prompt = output[-10:].split('\n')[-1]
        return output.strip(prompt).replace("--More-- \r         \r", "")

    def read_config_scp(self, destination):
        self.scp.get("sys_config", destination)

    def add_admin(self, username, password, privilege="prof_admin", role=None, sshkey=None, ssh_only_key=False,
                  verify=True):

        # TODO: remove redundant code
        # TODO: abstract privileges

        if role:
            raise ValueError("Roles not supported")

        if ssh_only_key:
            raise NotImplementedError("ssh_only_key not implemented")

        with self.ctx_config_block("system admin"):
            with self.ctx_edit_block(common.sanitize(username)):
                self.run_command("set password %s" % common.sanitize(password), True)
                self.run_command("set accprofile %s" % common.sanitize(privilege), True)
                self.run_command("set trusthost1 192.168.50.50 192.168.50.50", True)

            if sshkey:
                    self.run_command('set ssh-public-key1 "ssh-dss %s"' % sshkey, True)

        if verify:
            if not self.verify_login(username, password):
                raise common.OperationalError("Failed to add new admin")
            else:
                return True

    def enable_scp(self):
        with self.ctx_config_block("system global"):
            self.run_command("set admin-scp enable", True)

    def read_sysinfo(self):
        #with self.ctx_term_setup():
        if True:
            output = self.run_command("get system status")
            match = RE_SYSINFO.match(output)

            if match:
                return match.groupdict()

    @contextmanager
    def ctx_config_block(self, path):
        try:
            self.run_command("config " + path, in_block=True)
            yield
        finally:
            self.run_command("end")

    @contextmanager
    def ctx_edit_block(self, path):
        try:
            self.run_command("edit " + path, in_block=True)
            yield
        finally:
            self.run_command("next", in_block=True)

    def setup_terminal(self):
        #FIXME: does not work on $ prompt FG (vdoms?)
        with self.ctx_config_block('system console'):
            self.run_command("set output standard", True)

    def teardown_terminal(self):
        with self.ctx_config_block('system console'):
            self.run_command("set output more", True)

    def close(self):
        if self.chan:
            self.interact.send("exit")
        super(FortigateRemoteControl, self).close()


if __name__ == '__main__':
    import getpass
    rc = FortigateRemoteControl("c93f.continum.net", port=2222, timeout=1)
    rc.connect("root", getpass.getpass())