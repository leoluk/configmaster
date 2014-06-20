from django.db import models


class DeviceGroup(models.Model):
    name = models.CharField("Group name", max_length=100)
    enabled = models.BooleanField("Config management enabled for devices in group", default=True)

    def __unicode__(self):
        return self.name


class DeviceType(models.Model):
    name = models.CharField(max_length=100)
    handler = models.CharField("Device handler class", max_length=100, blank=True)

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

    group = models.ForeignKey(DeviceGroup, null=True, blank=True)
    device_type = models.ForeignKey(DeviceType, null=True, blank=True)

    data_model = models.CharField("Device model", max_length=100, blank=True)
    data_firmware = models.CharField("Firmware revision", max_length=100, blank=True)
    data_serial = models.CharField("Serial number", max_length=100, blank=True)

    def __unicode__(self):
        return self.name


class Report(models.Model):
    device = models.ForeignKey(Device, editable=False)
    date = models.DateTimeField(auto_now=True)

    RESULT_SUCCESS = 0
    RESULT_FAILURE = 1

    RESULT_CHOICES = (
        (RESULT_SUCCESS, "Success"),
        (RESULT_FAILURE, "Failure")
    )

    result = models.IntegerField(choices=RESULT_CHOICES, editable=False)
    output = models.TextField(editable=False)
