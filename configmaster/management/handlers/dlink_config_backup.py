import json
import socket
import urllib
from django.conf import settings
import requests
import os

from sh import git

from configmaster.management.handlers.base import BaseHandler, \
    TaskExecutionError
from configmaster.management.handlers.config_backup import \
    NetworkDeviceConfigBackupHandler
from configmaster.models import Repository, DeviceGroup


def recvall(sock):
    data = b''
    while True:
        packet = sock.recv(1024)
        if not packet:
            break
        data += packet
    return data


LOGIN_REQ = b'POST / HTTP/1.0\r\nContent-Length: %d\r\n' \
            b'Cache-Control: max-age=0\r\n\r\n%s'


class DLinkConfigBackupHandler(BaseHandler):
    def __init__(self, device):
        super(DLinkConfigBackupHandler, self).__init__(device)
        self.credential = self.device.get_credential()

    def _connect_sock(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.IPPROTO_TCP, socket.TCP_CORK, 1)
        s.connect((self.device.hostname, 80))
        return s

    def run(self, *args, **kwargs):
        if self.device.device_type.filter_expressions:
            raise NotImplementedError(
                "Config filter not implemented for this device type")

        login_data = urllib.urlencode({
            "Login": self.credential.username,
            "Password": self.credential.password,
            "BrowsingPage": "Smart_Wizard.htm",
            "currlang": 0,
            "changlang": 0
        })

        # D-Link DGS switches respond to a HTTP/1.0 POST request with a
        # HTTP 0.9-style response (no status line or headers, only content),
        # so we can't use python-requests (BadStatusLine exception) or urllib
        # (HTTP 0.9 support is deprecated and was removed in Python 3.4).
        # Do a raw HTTP request instead.

        s = self._connect_sock()
        s.sendall(LOGIN_REQ % (len(login_data), login_data))
        login_page = recvall(s).decode()
        s.close()

        try:
            token = login_page.split("Gambit=", 1)[1].split('"', 1)[0]
        except IndexError:
            raise TaskExecutionError("Login failed")

        config_url = "http://%s/config.bin?Gambit=%s" % \
                     (self.device.hostname, token)
        req = requests.get(config_url)

        if req.status_code != 200:
            raise TaskExecutionError(
                "Failed to download config (status code %d)" % req.status_code)

        self.device.group.repository.lock.acquire()

        # TODO: config backup task mixin (T173)

        filename = self.device.config_backup_filename.replace('.txt', '.bin')

        with open(filename, 'wb') as f:
            f.write(req.content)

        version_url = "http://%s/iss/specific/Device.js?Gambit=%s" % \
                      (self.device.hostname, token)
        req = requests.get(version_url)
        self.device.version_info = ' - '.join(json.loads(
            req.text.split("Switch_Status = ", 1)[1]
                .split(';', 1)[0].replace("'", '"'))[:2])
        self.device.save()

        # Git operations

        os.chdir(self.device.group.repository.path)

        if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
            return self._return_success("Config backup successful")

        # Commit config changes

        git.add('-u')
        commit_message = u"{} config change on {} ({})".format(
            self.device.group, self.device.label, self.device)
        changes = NetworkDeviceConfigBackupHandler._git_commit(commit_message)

        # Commit any new, previously untracked configs

        git.add('.')
        commit_message = u"{} config for {} added".format(
            self.device.group, self.device.label)
        changes |= NetworkDeviceConfigBackupHandler._git_commit(commit_message)

        self.device.group.repository.lock.release()

        return self._return_success("Config backup successful ({})".format(
            "no changes" if not changes else "changes found"
        ))

    def cleanup(self):
        if self.device.group.repository.lock.acquired:
            os.chdir(self.device.group.repository.path)
            git.reset('--hard')

    @classmethod
    def run_completed(cls):
        if settings.TASK_CONFIG_BACKUP_DISABLE_GIT:
            for repository in Repository.objects.all():
                repository.lock.release()
            return

        for repository in Repository.objects.all():
            repository.lock.acquire()

        for device_group in DeviceGroup.objects.all():
            os.chdir(device_group.repository.path)
            git.push()

        for repository in Repository.objects.all():
            repository.lock.release()
