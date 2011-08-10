# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'RecordSet', fields ['changeset', 'content_type', 'object_id']
        db.delete_unique('softdelete_recordset', ['changeset_id', 'content_type_id', 'object_id'])

        # Deleting model 'RecordSet'
        db.delete_table('softdelete_recordset')

        # Adding model 'SoftDeleteRecord'
        db.create_table('softdelete_softdeleterecord', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recordsets', to=orm['softdelete.ChangeSet'])),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('softdelete', ['SoftDeleteRecord'])

        # Adding unique constraint on 'SoftDeleteRecord', fields ['changeset', 'content_type', 'object_id']
        db.create_unique('softdelete_softdeleterecord', ['changeset_id', 'content_type_id', 'object_id'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'SoftDeleteRecord', fields ['changeset', 'content_type', 'object_id']
        db.delete_unique('softdelete_softdeleterecord', ['changeset_id', 'content_type_id', 'object_id'])

        # Adding model 'RecordSet'
        db.create_table('softdelete_recordset', (
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recordsets', to=orm['softdelete.ChangeSet'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('content_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['contenttypes.ContentType'])),
            ('created_date', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.utcnow)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('softdelete', ['RecordSet'])

        # Adding unique constraint on 'RecordSet', fields ['changeset', 'content_type', 'object_id']
        db.create_unique('softdelete_recordset', ['changeset_id', 'content_type_id', 'object_id'])

        # Deleting model 'SoftDeleteRecord'
        db.delete_table('softdelete_softdeleterecord')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'softdelete.changeset': {
            'Meta': {'object_name': 'ChangeSet'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'softdelete.softdeleterecord': {
            'Meta': {'unique_together': "(('changeset', 'content_type', 'object_id'),)", 'object_name': 'SoftDeleteRecord'},
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recordsets'", 'to': "orm['softdelete.ChangeSet']"}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'created_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.utcnow'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {})
        }
    }

    complete_apps = ['softdelete']
