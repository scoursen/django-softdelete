# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('softdelete', '0001_initial'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='changeset',
            index_together=set([('content_type', 'object_id')]),
        ),
        migrations.AlterIndexTogether(
            name='softdeleterecord',
            index_together=set([('content_type', 'object_id')]),
        ),
    ]
