#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from contextlib import contextmanager
from django.conf import settings
import paramiko
import re
from paramiko import SSHException
import socket

from configmaster.management.handlers import BaseHandler
from configmaster.models import Credential, DeviceType
from utils.remote.brocade import BrocadeRemoteControl
from utils.remote.common import GuessingFirewallRemoteControl, RemoteException, \
    NetworkDeviceRemoteControl
from utils.remote.fortigate import FortigateRemoteControl
from utils.remote.juniper import JuniperRemoteControl
from utils.remote.procurve import ProCurveRemoteControl
from utils.remote.unix import UnixRemoteControl

RE_MATCH_FIRST_WORD = re.compile(r'\b\w+\b')


class SSHDeviceHandler(BaseHandler):
    def __init__(self, device):
        """
        A base class for SSH device handlers. Provides self.credential and
        handles the most common OS and Paramiko connection errors. Does not
        provide any connection facilities.

        :type device: configmaster.models.Device
        """

        super(SSHDeviceHandler, self).__init__(device)
        self.credential = self.device.get_credential()
        if not self.device.device_type.connection_setting:
            self._fail("No connection setting for device")
        elif not (self.device.device_type.connection_setting.ssh_port or
                      self.device.device_type.connection_setting.use_ssh_config):
            self._fail("Invalid SSH port setting")

        if not self.credential or self.credential.type != Credential.TYPE_PLAINTEXT:
            self._fail("No valid credential for device")

    @contextmanager
    def _catch_connection_errors(self):
        try:
            yield

        # Handle network/connections errors (all other errors will be caught
        # by the task runner and reported with full traceback).

        except socket.timeout, e:
            self._fail("Client error: Socket timeout")
        except socket.error, e:
            if e.strerror is None:
                # In some cases, a socket error without any message is raised.
                # This would result in an useless, empty error message, so
                # we'll re-raise the exception instead to get a nice traceback.
                raise e
            self._fail("Socket error: %s" % e.strerror)
        except (RemoteException, SSHException), e:
            self._fail("Client error: %s" % str(e))

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(SSHDeviceHandler, self).run_wrapper(*args, **kwargs):
            with self._catch_connection_errors():
                yield


class NetworkDeviceHandler(SSHDeviceHandler):
    RC_CLASSES = {
        u"Fortigate": FortigateRemoteControl,
        u"Juniper SSG": JuniperRemoteControl,
        u"HP ProCurve": ProCurveRemoteControl,
        u"Brocade *Iron": BrocadeRemoteControl,
        u"*NIX": UnixRemoteControl,
    }

    def __init__(self, device):
        """
        A base class for SSH-based network device handlers. Chooses the right
        remote control class, instantiates it as self.connection and
        connects and authenticates with the device using the credential
        from the database.
        """
        super(NetworkDeviceHandler, self).__init__(device)

        self.connection = self._get_fw_remote_control()
        """:type : NetworkDeviceRemoteControl"""

    @property
    def _remote_control_class(self):
        """
        Returns the correct remote control class. The device type <->
        class mapping is defined in the FW_RC_CLASSES dictionary.
        """
        try:
            return self.RC_CLASSES[unicode(self.device.device_type.name)]
        except KeyError:
            self._fail("No device controller for device type %s",
                       self.device.device_type)


    # noinspection PyTypeChecker
    def _get_fw_remote_control(self, *args, **kwargs):
        """
        Instantiates and returns the correct remote controller for the        # noinspection PyTypeChecker
        device's device_type.

        :rtype : NetworkDeviceRemoteControl
        """

        ssh_hostname, ssh_port = self.device.get_ssh_connection_info()

        return self._remote_control_class(
            ssh_hostname,
            ssh_port,
            hostkey_change_cb=self.device.approve_new_hostkey,
            *args, **kwargs)

    def _connect_ssh(self):
        """
        Does the SSH login and connection setup. This method can be
        overwritten by descendant classes to customize the login behaviour.
        """
        self.connection.connect(self.credential.username,
                                self.credential.password)

    @contextmanager
    def run_wrapper(self, *args, **kwargs):
        with super(NetworkDeviceHandler, self).run_wrapper(*args, **kwargs):
            self._connect_ssh()
            try:
                yield
            finally:
                self.connection.close()


class SSHLoginTestHandler(NetworkDeviceHandler):
    def _connect_ssh(self):
        # ProCurve switches close the channel if a shell without TTY is
        # requested.
        self.connection.allocate_pty = True
        super(SSHLoginTestHandler, self)._connect_ssh()

    @property
    def _remote_control_class(self):
        return NetworkDeviceRemoteControl

    def run(self):
        return self._return_success("Login successful")


class GuessFirewallTypeHandler(NetworkDeviceHandler):
    def __init__(self, device):
        """
        This handler guesses the Firewall type. Right now, it detects
        Juniper SSG firewalls and simply assumes that everything else is a
        Fortigate firewall. The correct device type is assigned to the
        device if it was successfully guessed.

        This task is quite useful if you assign it to a catch-all device type
        for imported firewalls.
        """

        super(GuessFirewallTypeHandler, self).__init__(device)

    @property
    def _remote_control_class(self):
        # Bypass the automatic mapping
        return GuessingFirewallRemoteControl

    def run(self):
        guess = self.connection.guess_type()

        if not guess:
            self._fail("Could not guess Firewall type")
        else:
            device_type = DeviceType.objects.get(name=guess)
            self.device.device_type = device_type
            self.device.save()
            return self._return_success("Guess: %s", guess)

