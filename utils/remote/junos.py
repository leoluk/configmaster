#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import re

from utils.remote import common
from utils.remote.common import RemoteException

RE_TIME = re.compile(r'Current time: ([0-9-: ]+) UTC')


class JunosRemoteControl(common.NetworkDeviceRemoteControl):
    def __init__(self, *args, **kwargs):
        super(JunosRemoteControl, self).__init__(*args, **kwargs)
        self.allocate_pty = False
        self._date_format = '%Y-%m-%d %H:%M:%S'

    def read_config(self, startup_config=False):
        if startup_config:
            raise NotImplementedError

        return self.exec_command('show configuration')

    def get_raw_time(self):
        output = self.exec_command('show system uptime')
        line = output.split('\n')[0]
        return RE_TIME.findall(output)[0]
