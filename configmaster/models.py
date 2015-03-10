import logging
from django.conf import settings
import re
from django.contrib.auth.models import Group

from django.db import models
import django_auth_ldap.backend


logger = logging.getLogger(__name__)


def update_user_from_ldap(sender, user=None, ldap_user=None, **kwargs):
    try:
        name = ldap_user.attrs.get('displayname', [])
        uid = ldap_user.attrs.get('uid')[0]  # may not be empty

        user.groups.clear()

        for groupname in ldap_user.group_names:
            group = Group.objects.get_or_create(name=groupname)[0]
            group.user_set.add(user)

        user.password = "!"
        user.is_staff = True
        user.is_active = ([group in settings.LOGIN_ALLOWED_GROUPS for group in
                    ldap_user.group_names])

        if name:
            words = name[0].split()
            user.first_name = ' '.join(words[:-1])
            user.last_name = words[-1]

        if not str(user.email):
            user.email = uid + '@continum.net'
    except:
        logger.exception("LDAP update failed")
        return True


django_auth_ldap.backend.populate_user.connect(update_user_from_ldap)


class Credential(models.Model):
    TYPE_PLAINTEXT = 1
    TYPE_SSH = 2

    TYPE_CHOICES = (
        (TYPE_PLAINTEXT, "Plain text username/password combination"),
        (TYPE_SSH, "Path to a SSH public/private key pair")
    )

    type = models.IntegerField(choices=TYPE_CHOICES)

    description = models.CharField(max_length=100)

    username = models.CharField(max_length=100, null=True, blank=True)
    password = models.CharField(max_length=100, null=True, blank=True)

    path = models.CharField(max_length=300, null=True, blank=True)


    def __unicode__(self):
        return self.description


class ConnectionSetting(models.Model):
    name = models.CharField(max_length=100)
    ssh_port = models.IntegerField(verbose_name="SSH port", null=True, blank=True)
    use_ssh_config = models.BooleanField(verbose_name="Use ssh_config",
                                         default=False)

    def __unicode__(self):
        if self.ssh_port:
            return "{} (SSH: port {})".format(self.name, self.ssh_port)
        else:
            return self.name


class Repository(models.Model):
    class Meta:
        verbose_name_plural = "Repositories"

    name = models.CharField(max_length=100)
    path = models.CharField(max_length=500)

    def __unicode__(self):
        return u"{} - {}".format(self.name, self.path)


class DeviceGroup(models.Model):
    name = models.CharField("Group name", max_length=100)
    plural = models.CharField(max_length=100)
    enabled = models.BooleanField("Config management enabled for devices in group", default=True)
    default_device_type = models.ForeignKey("DeviceType", null=True, blank=True)
    repository = models.ForeignKey(Repository)

    def __unicode__(self):
        return self.name


class Task(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    class_name = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    hide_if_successful = models.BooleanField(
        default=False,
        help_text="Hide in frontend if the task was successful or the "
                  "device is disabled.")
    result_url = models.CharField(max_length=100, verbose_name="Result URL", null=True, blank=True,
                                  help_text="A URL which points to the result of a task. Will be displayed in "
                                            "the frontend if the task has been successfully run at least once. "
                                            "<br/>The following placeholders are available: {label}, {hostname}, "
                                            "{device_type}, {group} and {group_plural}.")

    def __unicode__(self):
        return self.name

    def get_formatted_result_url(self, device):
        """
        :type device: Device
        """
        return self.result_url.format(
            label=device.label,
            hostname=device.hostname,
            device_type=device.device_type,
            group=device.group,
            group_plural=device.group.plural.replace(' ', '')
        )


class DeviceType(models.Model):
    name = models.CharField(max_length=100)
    tasks = models.ManyToManyField(Task, null=True, blank=True)

    connection_setting = models.ForeignKey(ConnectionSetting, null=True, blank=True)
    credential = models.ForeignKey(Credential, help_text="Default credential for this device type", null=True,
                                   blank=True)

    config_filter = models.TextField(help_text="List of regular expressions, one per line. "
                                               "Content matched by one of the expressions will "
                                               "be removed from config files before they are committed.<br/>"
                                               "Dot does not match newlines, ^$ match the beginning "
                                               "and end of each line.", blank=True)

    def __init__(self, *args, **kwargs):
        super(DeviceType, self).__init__(*args, **kwargs)
        self._filter_expressions = []

    @property
    def filter_expressions(self):
        """
        Return the config_filter field as a list of compiled regular
        expressions. A simple cache is used to avoid re-compilation on every
        access.
        """
        if not self._filter_expressions and len(self.config_filter):
            for regex in self.config_filter.splitlines():
                self._filter_expressions.append(re.compile(regex, flags=re.MULTILINE))

        return self._filter_expressions

    def __unicode__(self):
        return self.name


class Device(models.Model):

    STATUS_DISABLED = 1
    STATUS_SUCCESS = 2
    STATUS_NO_REPORT = 3
    STATUS_ERROR = 4

    STATUS_CHOICES = (
        (STATUS_DISABLED, "Disabled"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_NO_REPORT, "No report"),
        (STATUS_ERROR, "Error")
    )

    name = models.CharField("Device name", max_length=100, blank=True)
    label = models.CharField("Service label", max_length=4, unique=True)
    hostname = models.CharField("Host name", max_length=200, blank=True)

    enabled = models.BooleanField("Config management enabled", default=True)
    sync = models.BooleanField("Synchronized with PWSafe", default=True, help_text="Disabling this flag does not "
                                                                                   "disable the synchronization for this "
                                                                                   "device. Certain fields cannot be "
                                                                                   "edited if this flag is set.")

    do_not_use_scp = models.BooleanField(help_text='Use an interactive SSH session instead of SCP. '
                                                   'For Fortigate devices, this is a "feature of '
                                                   'last resort" (incomplete config).',
                                         verbose_name="Do not use SCP", default=False)
    credential = models.ForeignKey(Credential, help_text="Overrides group default.", null=True, blank=True)

    group = models.ForeignKey(DeviceGroup, null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, null=True, blank=True)

    data_model = models.CharField("Device model", max_length=100, blank=True)
    data_firmware = models.CharField("Firmware revision", max_length=100, blank=True)
    data_serial = models.CharField("Serial number", max_length=100, blank=True)

    # Paramiko is configured to use the OpenSSH known_hosts file. This flag
    # is needed because CM runs are non- interactive by default, so we need
    # another way to approve host key changes.

    ssh_known_host = models.BooleanField(verbose_name="SSH known host", default=False,
                                         help_text="This flag is set after the SSH key has been added to the "
                                                   "server's host key database. Unset it manually to accept a "
                                                   "changed host key.")

    def __unicode__(self):
        return self.name if self.name else self.hostname

    def is_enabled(self):
        return self.enabled and self.group.enabled

    @property
    def asset_db_url(self):
        return settings.PWSAFE_ASSETDB_REDIRECT % self.label

    @property
    def pwsafe_url(self):
        return settings.PWSAFE_DEVICE_URL % self.label

    @property
    def number_of_successful_runs(self):
        return self.report_set.filter(result=Report.RESULT_SUCCESS).count()

    def get_latest_report_for_task(self, task):
        try:
            report = self.report_set.filter(task=task).latest()
        except Report.DoesNotExist:
            report = None
        return report

    @property
    def latest_reports(self):
        """
        Generate a list of (task, status, report) tuples with the latest
        report for each assigned task of the device.

        Called from the dashboard view template.
        """
        reports = []
        if not self.device_type:
            return
        for task in self.device_type.tasks.all():
            report = self.get_latest_report_for_task(task)
            status = self.get_status_for_report(report)
            if (task.hide_if_successful and status in (self.STATUS_SUCCESS,
                                                       self.STATUS_DISABLED)):
                continue
            reports.append((task, status, report))
        return reports

    def get_status_for_report(self, report):
        if not self.is_enabled():
            return self.STATUS_DISABLED

        if not report:
            return self.STATUS_NO_REPORT

        if report.result_is_success():
            return self.STATUS_SUCCESS
        else:
            return self.STATUS_ERROR


class Report(models.Model):
    class Meta:
        get_latest_by = "date"

    device = models.ForeignKey(Device, editable=False)
    task = models.ForeignKey(Task, editable=False)
    date = models.DateTimeField(auto_now=True)

    RESULT_SUCCESS = 0
    RESULT_FAILURE = 1

    RESULT_CHOICES = (
        (RESULT_SUCCESS, "Success"),
        (RESULT_FAILURE, "Failure")
    )

    result = models.IntegerField(choices=RESULT_CHOICES, editable=False)
    output = models.TextField(editable=False)
    long_output = models.TextField(editable=False, null=True)

    def result_is_success(self):
        return self.result == Report.RESULT_SUCCESS

    @property
    def result_url(self):
        return self.task.get_formatted_result_url(self.device)
