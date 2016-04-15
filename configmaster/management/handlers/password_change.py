#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from configmaster.management.handlers.network_device import \
    NetworkDeviceHandler


class PasswordChangeHandler(NetworkDeviceHandler):
    """
    Special handler which implements password changes for
    PasswordChangeAPIView.

    Incompatible with task runner!
    """

    def __init__(self, device, current_password, new_password, username):
        super(PasswordChangeHandler, self).__init__(device)
        self.username = username
        self.new_password = new_password
        self.current_password = current_password

    def run(self, *args, **kwargs):
        self.connection.change_admin_password(
            self.new_password, verify=True)

        return self._return_success("Password successfully changed")

    def _connect_ssh(self):
        """
        We override the default connection method since we don't want to use
        the default
        """
        self.connection.connect(self.username, self.current_password)
