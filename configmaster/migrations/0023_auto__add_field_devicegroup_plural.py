# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'DeviceGroup.plural'
        db.add_column(u'configmaster_devicegroup', 'plural',
                      self.gf('django.db.models.fields.CharField')(default='Fixme', max_length=100),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'DeviceGroup.plural'
        db.delete_column(u'configmaster_devicegroup', 'plural')


    models = {
        u'configmaster.connectionsetting': {
            'Meta': {'object_name': 'ConnectionSetting'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ssh_port': ('django.db.models.fields.IntegerField', [], {})
        },
        u'configmaster.credential': {
            'Meta': {'object_name': 'Credential'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        },
        u'configmaster.device': {
            'Meta': {'object_name': 'Device'},
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.Credential']", 'null': 'True', 'blank': 'True'}),
            'data_firmware': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'data_model': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'data_serial': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'device_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceType']", 'null': 'True', 'blank': 'True'}),
            'do_not_use_scp': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceGroup']", 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'ssh_known_host': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'configmaster.devicegroup': {
            'Meta': {'object_name': 'DeviceGroup'},
            'default_device_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceType']", 'null': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plural': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'configmaster.devicetype': {
            'Meta': {'object_name': 'DeviceType'},
            'config_filter': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'connection_setting': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.ConnectionSetting']", 'null': 'True', 'blank': 'True'}),
            'credential': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.Credential']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tasks': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'to': u"orm['configmaster.Task']", 'null': 'True', 'blank': 'True'})
        },
        u'configmaster.report': {
            'Meta': {'object_name': 'Report'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'device': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.Device']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'long_output': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'output': ('django.db.models.fields.TextField', [], {}),
            'result': ('django.db.models.fields.IntegerField', [], {}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.Task']"})
        },
        u'configmaster.task': {
            'Meta': {'object_name': 'Task'},
            'class_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'result_url': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['configmaster']