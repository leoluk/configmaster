# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AccessConfig'
        db.create_table(u'configmaster_accessconfig', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ssh_port', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal(u'configmaster', ['AccessConfig'])

        # Adding field 'DeviceType.access_config'
        db.add_column(u'configmaster_devicetype', 'access_config',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configmaster.AccessConfig'], null=True, blank=True),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting model 'AccessConfig'
        db.delete_table(u'configmaster_accessconfig')

        # Deleting field 'DeviceType.access_config'
        db.delete_column(u'configmaster_devicetype', 'access_config_id')


    models = {
        u'configmaster.accessconfig': {
            'Meta': {'object_name': 'AccessConfig'},
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
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceGroup']", 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'label': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '4'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'sync': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        u'configmaster.devicegroup': {
            'Meta': {'object_name': 'DeviceGroup'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'configmaster.devicetype': {
            'Meta': {'object_name': 'DeviceType'},
            'access_config': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.AccessConfig']", 'null': 'True', 'blank': 'True'}),
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
            'output': ('django.db.models.fields.TextField', [], {}),
            'result': ('django.db.models.fields.IntegerField', [], {}),
            'task': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.Task']"})
        },
        u'configmaster.task': {
            'Meta': {'object_name': 'Task'},
            'class_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['configmaster']