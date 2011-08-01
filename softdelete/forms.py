from django.forms import *
from softdelete.models import *

class ChangeSetForm(ModelForm):
    class Meta:
        model = ChangeSet
        exclude = ('content_type', 'object_id',)
