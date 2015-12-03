from django.forms import *
from softdelete.models import *
import logging


class ChangeSetForm(ModelForm):
    class Meta:
        model = ChangeSet
        exclude = ('content_type', 'object_id',)
