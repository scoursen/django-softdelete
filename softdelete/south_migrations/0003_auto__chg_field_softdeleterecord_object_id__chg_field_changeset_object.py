# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'SoftDeleteRecord.object_id'
        db.alter_column(u'softdelete_softdeleterecord', 'object_id', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Changing field 'ChangeSet.object_id'
        db.alter_column(u'softdelete_changeset', 'object_id', self.gf('django.db.models.fields.CharField')(max_length=100))

    def backwards(self, orm):

        # Changing field 'SoftDeleteRecord.object_id'
        db.alter_column(u'softdelete_softdeleterecord', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')())

        # Changing field 'ChangeSet.object_id'
        db.alter_column(u'softdelete_changeset', 'object_id', self.gf('django.db.models.fields.PositiveIntegerField')())

    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'softdelete.changeset': {
            'Meta': {'object_name': 'ChangeSet'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'softdelete.softdeleterecord': {
            'Meta': {'unique_together': "(('changeset', 'content_type', 'object_id'),)", 'object_name': 'SoftDeleteRecord'},
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'soft_delete_records'", 'to': u"orm['softdelete.ChangeSet']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['softdelete']