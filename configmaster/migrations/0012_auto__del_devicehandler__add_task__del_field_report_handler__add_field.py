# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting model 'DeviceHandler'
        db.delete_table(u'configmaster_devicehandler')

        # Adding model 'Task'
        db.create_table(u'configmaster_task', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('class_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'configmaster', ['Task'])

        # Deleting field 'Report.handler'
        db.delete_column(u'configmaster_report', 'handler_id')

        # Adding field 'Report.task'
        db.add_column(u'configmaster_report', 'task',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['configmaster.Task']),
                      keep_default=False)

        # Removing M2M table for field handler on 'DeviceType'
        db.delete_table(db.shorten_name(u'configmaster_devicetype_handler'))

        # Adding M2M table for field tasks on 'DeviceType'
        m2m_table_name = db.shorten_name(u'configmaster_devicetype_tasks')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('devicetype', models.ForeignKey(orm[u'configmaster.devicetype'], null=False)),
            ('task', models.ForeignKey(orm[u'configmaster.task'], null=False))
        ))
        db.create_unique(m2m_table_name, ['devicetype_id', 'task_id'])


    def backwards(self, orm):
        # Adding model 'DeviceHandler'
        db.create_table(u'configmaster_devicehandler', (
            ('class_name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal(u'configmaster', ['DeviceHandler'])

        # Deleting model 'Task'
        db.delete_table(u'configmaster_task')

        # Adding field 'Report.handler'
        db.add_column(u'configmaster_report', 'handler',
                      self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['configmaster.DeviceHandler']),
                      keep_default=False)

        # Deleting field 'Report.task'
        db.delete_column(u'configmaster_report', 'task_id')

        # Adding M2M table for field handler on 'DeviceType'
        m2m_table_name = db.shorten_name(u'configmaster_devicetype_handler')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('devicetype', models.ForeignKey(orm[u'configmaster.devicetype'], null=False)),
            ('devicehandler', models.ForeignKey(orm[u'configmaster.devicehandler'], null=False))
        ))
        db.create_unique(m2m_table_name, ['devicetype_id', 'devicehandler_id'])

        # Removing M2M table for field tasks on 'DeviceType'
        db.delete_table(db.shorten_name(u'configmaster_devicetype_tasks'))


    models = {
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