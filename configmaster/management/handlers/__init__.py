#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

"""
Each task in the database invokes a handler. Handlers contain the high-level
implementations of a task and usually invoke external libraries like those
found in :mod:`utils.remote`.

They are invoked by :mod:`configmaster.management.commands.run`.
"""

# Import all "public" task handlers here. Tasks handlers not imported
# here cannot be directly invoked.

from base import BaseHandler
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler
from network_device import GuessFirewallTypeHandler, \
    SSHLoginTestHandler
from config_compare import NetworkDeviceCompareWithStartupHandler
from dlink_config_backup import DLinkConfigBackupHandler
from ntp import NetworkDeviceNTPHandler
