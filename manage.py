#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "configmaster_project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
