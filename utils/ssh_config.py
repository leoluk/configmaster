#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

from django.conf import settings
import paramiko

__author__ = 'lschabel'


def lookup_host_in_ssh_config(hostname):
    parser = paramiko.SSHConfig()
    parser.parse(open(settings.TASK_CONFIG_BACKUP_SSH_CONFIG))
    config = parser.lookup(hostname)
    if 'port' in config:
        ssh_port = int(config['port'])
    else:
        ssh_port = 22
    if 'hostname' in config:
        ssh_hostname = config['hostname']
    else:
        ssh_hostname = hostname
    return ssh_hostname, ssh_port
