# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DeviceGroup'
        db.create_table(u'configmaster_devicegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal(u'configmaster', ['DeviceGroup'])

        # Adding model 'Device'
        db.create_table(u'configmaster_device', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('label', self.gf('django.db.models.fields.CharField')(unique=True, max_length=4)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configmaster.DeviceGroup'])),
            ('device_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['configmaster.DeviceType'])),
        ))
        db.send_create_signal(u'configmaster', ['Device'])

        # Adding model 'DeviceType'
        db.create_table(u'configmaster_devicetype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('handler', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'configmaster', ['DeviceType'])


    def backwards(self, orm):
        # Deleting model 'DeviceGroup'
        db.delete_table(u'configmaster_devicegroup')

        # Deleting model 'Device'
        db.delete_table(u'configmaster_device')

        # Deleting model 'DeviceType'
        db.delete_table(u'configmaster_devicetype')


    models = {
        u'configmaster.device': {
            'Meta': {'object_name': 'Device'},
            'device_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceType']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['configmaster.DeviceGroup']"}),
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
            'handler': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['configmaster']