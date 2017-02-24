#!/usr/bin/env python2
# -*- coding: utf8 -*-
#
#   Copyright (C) 2013-2016 Continum AG
#

import tempfile

from django.conf import settings
from django.core.management import BaseCommand
import re
import requests
import os
import sh
import shutil
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler

from utils import locking

RE_MATCH_SINGLE_WORD = re.compile(r'\A[\w-]+\Z')


class Command(BaseCommand):
    """
    This management command backs up and versions ESXi servers by downloading
    the exported config files from a web server. The actual config file export
    is not handled by ConfigMaster, only the versioning and alerting part.

    This command is designed to be invoked by a cronjob, just as the regular
    run command (make sure to keep the config file export task in sync!).

    It is NOT integrated with the ConfigMaster task runner or database since
    it works very differently from network device config backups. All hosts
    are hardcoded in the config file for now since we don't want to  import
    ESXi servers into the database for now.
    """

    help = "ESXi backup run"

    def __init__(self):
        super(Command, self).__init__()

    def handle(self, *args, **options):
        session = requests.session()
        session.verify = False  # internal network, self-signed cert
        session.headers['User-Agent'] = 'python-requests/ConfigMaster'

        # global lock - remove after Repository integration is done
        global_lock = locking.FileLock("/run/configmaster-esxi-backup")
        global_lock.acquire()

        for name, uri in settings.ESXI_BACKUP:
            self.stdout.write("Acquiring lock for %s..." % name)
            run_lock = locking.FileLock("/run/esxi-%s" % name)
            tempdir = tempfile.mkdtemp('esxi')
            self.stdout.write("Lock acquired, running... (%s)" % tempdir)

            try:
                run_lock.acquire(non_blocking=True)
            except IOError:
                self.stderr.write(
                    "A run is already in progress")
                return

            try:
                resp = session.get(uri, timeout=5)
            except IOError as e:
                self.stderr.write(
                    "Config backup failure for %s: %s" % (name, str(e)))
                continue

            if resp.status_code != 200:
                self.stderr.write(
                    "Config backup failed for %s: %r" % (name, resp.content))
                continue

            stage_1 = os.path.join(tempdir, 'stage1.tgz')

            with open(stage_1, 'wb') as f:
                f.write(resp.content)

            os.chdir(tempdir)

            try:
                stage1_ret = sh.aunpack('stage1.tgz')
            except sh.ErrorReturnCode:
                self.stderr.write(
                    "Config backup failed for %s: failed to unpack stage1"
                    % name)
                continue

            if not "\nstate.tgz" in stage1_ret.stdout or not os.path.exists(
                    'stage1'):
                self.stderr.write(
                    "Config backup failed for %s: invalid stage1" % name)
                continue

            os.chdir('stage1')

            try:
                stage2_ret = sh.aunpack('state.tgz')
            except sh.ErrorReturnCode:
                self.stderr.write(
                    "Config backup failed for %s: failed to unpack state.tgz"
                    % name)
                continue

            if not os.path.exists('local.tgz'):
                self.stderr.write(
                    "Config backup failed for %s: invalid state.tgz, "
                    "local.tgz missing" % name)
                continue

            try:
                stage3_ret = sh.aunpack('local.tgz')
            except sh.ErrorReturnCode:
                self.stderr.write(
                    "Config backup failed for %s: "
                    "failed to unpack local.tgz" % name)
                continue

            if not os.path.exists('etc'):
                self.stderr.write(
                    "Config backup failed for %s: "
                    "invalid local.tgz, etc/ missing" % name)
                continue

            for path in settings.ESXI_FILE_BLACKLIST:
                if os.path.exists(path):
                    os.unlink(path)

            repo_dir = os.path.join(settings.ESXI_BACKUP_REPO, name)

            if not os.path.exists(repo_dir):
                os.mkdir(repo_dir)

            sh.sh('-c', '/usr/bin/find -type d -exec chmod 750 {} \;'.split())
            sh.sh('-c', '/usr/bin/find -type d -exec chmod 640 {} \;'.split())

            for root, dirs, files in os.walk(repo_dir):
                for d in dirs:
                    os.chmod(os.path.join(root,d), 0o750)
                for f in files:
                    os.chmod(os.path.join(root,f), 0o640)

            sh.cp('-r', '.', repo_dir+'/')
            os.chdir(repo_dir)

            try:
                sh.git.add('-u', '.')
                sh.git.add('.')
                if NetworkDeviceConfigBackupHandler._git_commit(
                                "ESXi config change (%s)" % name):
                    sh.git.push()
            except sh.ErrorReturnCode as e:
                self.stderr.write(
                    "Git commit or push failed: " + str(e))
                continue

            sh.cp(
                os.path.join(tempdir, 'stage1.tgz'),
                os.path.join(settings.ESXI_BACKUP_REPO_RAW, '%s.tgz' % name)
            )

            os.chdir(settings.ESXI_BACKUP_REPO_RAW)

            try:
                sh.git.add('-u', '.')
                sh.git.add('.')
                if NetworkDeviceConfigBackupHandler._git_commit(
                                "ESXi raw config change (%s)" % name):
                    sh.git.push()
            except sh.ErrorReturnCode as e:
                self.stderr.write(
                    "Git commit or push failed: " + str(e))
                continue

            shutil.rmtree(tempdir)
            run_lock.release()

        for path in (settings.ESXI_BACKUP_REPO_RAW, settings.ESXI_BACKUP_REPO):
            os.chdir(path)
            sh.git.push()

        global_lock.release()
        self.stdout.write("Run completed.")
