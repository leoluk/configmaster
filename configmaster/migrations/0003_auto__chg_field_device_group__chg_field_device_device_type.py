# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Device.group'
        db.alter_column(u'configmaster_device', 'group_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configmaster.DeviceGroup'], null=True))

        # Changing field 'Device.device_type'
        db.alter_column(u'configmaster_device', 'device_type_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configmaster.DeviceType'], null=True))

    def backwards(self, orm):

        # Changing field 'Device.group'
        db.alter_column(u'configmaster_device', 'group_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['configmaster.DeviceGroup']))

        # Changing field 'Device.device_type'
        db.alter_column(u'configmaster_device', 'device_type_id', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['configmaster.DeviceType']))

    models = {
        u'configmaster.device': {
            'Meta': {'object_name': 'Device'},
            'device_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceType']", 'null': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceGroup']", 'null': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'configmaster.devicegroup': {
            'Meta': {'object_name': 'DeviceGroup'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'configmaster.devicetype': {
            'Meta': {'object_name': 'DeviceType'},
            'handler': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['configmaster']