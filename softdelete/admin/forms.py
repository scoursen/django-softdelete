from django.forms import *
from softdelete.models import *
from softdelete.forms import *
import logging

class SoftDeleteObjectAdminForm(ModelForm):
    deleted = BooleanField(required=False)
    
    class Meta:
        model = SoftDeleteObject
        exclude = ('deleted_flag',)

    def __init__(self, *args, **kwargs):
        super(SoftDeleteObjectAdminForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.initial['deleted'] = instance.deleted_flag

    def clean(self, *args, **kwargs):
        logging.info("in SoftDeleteObjectAdminForm.clean: %s, %s" % (args, kwargs))
        cleaned_data = super(SoftDeleteObjectAdminForm, self).clean(*args, **kwargs)
        logging.info("self.data.keys(): %s" % ( self.data.keys()))
        if self.data.has_key('undelete'):
            self.instance.deleted = False
            cleaned_data['deleted'] = False
            logging.info('undelete %s' % self.instance)
        logging.info("cleaned_data: %s" % cleaned_data)
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):
        model = super(SoftDeleteObjectAdminForm, self).save(commit=False, 
                                                            *args, **kwargs)
        model.deleted = self.cleaned_data['deleted']
        if commit:
            model.save()
        return model

class ChangeSetAdminForm(ChangeSetForm):
    pass

class SoftDeleteRecordAdminForm(ModelForm):
    class Meta:
        model = SoftDeleteRecord
        readonly_fields = ('created', )
        exclude = ('content_type', 'object_id', 'changeset')

