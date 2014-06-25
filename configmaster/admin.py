from django.contrib import admin
from django import forms
from configmaster.models import DeviceType, DeviceGroup, Report, Credential, Task, ConnectionSetting
from configmaster.models import Device


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("label", "name", "hostname", "group", "device_type", "enabled")
    list_filter = ("group", "device_type")
    search_fields = ("name", "hostname")

    fieldsets = (
        ("Basic info", {
            'fields': ('name', 'label', 'group', 'device_type')
        }),
        ("Settings", {
            'fields': ('enabled', 'sync', 'credential', 'ssh_known_host')
        }),
        ('Config management data', {
            'description': "Will get overwritten during the next run.",
            'fields': ('data_model', 'data_firmware', 'data_serial'),
        })
    )


    def get_readonly_fields(self, request, obj=None):
        fields = super(DeviceAdmin, self).get_readonly_fields(request, obj)

        if obj:
            if obj.sync:
                return "label", "name", "hostname", "group"

        return fields


class ReportAdmin(admin.ModelAdmin):
    readonly_fields = ("device", "date", "task", "result", "output", "long_output")
    list_display = ("date", "device", "task", "result", "output")
    list_filter = ("result",)


class CredentialAdminForm(forms.ModelForm):
    class Meta:
        model = Credential

    new_password = forms.CharField(required=False,
                                   label="Set password",
                                   help_text="Set new password for this entry. "
                                             "Leave empty to keep existing password.",
                                   widget=forms.TextInput(
                                       attrs={'class': 'vTextField'}))


class CredentialAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {
            'fields': ('description', 'type',),
        }),
        ('Plaintext login', {
            'fields': ('username', 'new_password'),
        }),
        ("SSH login", {
            'fields': ('path',)
        })
    )

    form = CredentialAdminForm

    list_display = ("description", "type", "username", "path")
    list_filter = ("type", )

    def save_model(self, request, obj, form, change):
        new_password = form.cleaned_data['new_password']

        # Ignore passwords consisting only of whitespace (prevent accidental overwrite).
        if len(new_password.strip()):
            obj.password = new_password

        obj.save()


admin.site.register(Device, DeviceAdmin)
admin.site.register(DeviceType)
admin.site.register(DeviceGroup)
admin.site.register(Task)
admin.site.register(ConnectionSetting)
admin.site.register(Credential, CredentialAdmin)
admin.site.register(Report, ReportAdmin)
