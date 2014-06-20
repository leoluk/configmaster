from django.db import models


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


class DeviceGroup(models.Model):
    name = models.CharField("Group name", max_length=100)
    enabled = models.BooleanField("Config management enabled for devices in group", default=True)


    def __unicode__(self):
        return self.name


class DeviceHandler(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    class_name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class DeviceType(models.Model):
    name = models.CharField(max_length=100)
    handler = models.ManyToManyField(DeviceHandler, null=True, blank=True)

    credential = models.ForeignKey(Credential, help_text="Default credential for this device type", null=True,
                                   blank=True)
    def __unicode__(self):
        return self.name


class Device(models.Model):
    name = models.CharField("Device name", max_length=100, blank=True)
    label = models.CharField("Service label", max_length=4, unique=True)
    hostname = models.CharField("Host name", max_length=200, blank=True)

    enabled = models.BooleanField("Config management enabled", default=True)
    sync = models.BooleanField("Synchronized with PWSafe", default=True, help_text="Disabling this flag does not "
                                                                                   "disable the synchronization for this "
                                                                                   "device. Certain fields cannot be "
                                                                                   "edited if this flag is set.")

    credential = models.ForeignKey(Credential, help_text="Overrides group default.", null=True, blank=True)

    group = models.ForeignKey(DeviceGroup, null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, null=True, blank=True)

    data_model = models.CharField("Device model", max_length=100, blank=True)
    data_firmware = models.CharField("Firmware revision", max_length=100, blank=True)
    data_serial = models.CharField("Serial number", max_length=100, blank=True)

    def __unicode__(self):
        return self.name


class Report(models.Model):
    device = models.ForeignKey(Device, editable=False)
    handler = models.ForeignKey(DeviceHandler, editable=False)
    date = models.DateTimeField(auto_now=True)

    RESULT_SUCCESS = 0
    RESULT_FAILURE = 1

    RESULT_CHOICES = (
        (RESULT_SUCCESS, "Success"),
        (RESULT_FAILURE, "Failure")
    )

    result = models.IntegerField(choices=RESULT_CHOICES, editable=False)
    output = models.TextField(editable=False)


