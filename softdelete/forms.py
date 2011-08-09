from django.forms import *
from softdelete.models import *
import logging

class ChangeSetForm(ModelForm):
    class Meta:
        model = ChangeSet
        exclude = ('content_type', 'object_id',)

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

    def save(self, commit=True, *args, **kwargs):
        model = super(SoftDeleteObjectAdminForm, self).save(commit=False, 
                                                            *args, **kwargs)
        model.deleted = self.cleaned_data['deleted']
        if commit:
            model.save()
        return model

class ChangeSetAdminForm(ChangeSetForm):
    def clean(self, *args, **kwargs):
        logging.info("in apikeyprofileform.clean: %s, %s" % (args, kwargs))
        cleaned_data = super(ChangeSetAdminForm, self).clean(*args, **kwargs)
        logging.info("cleaned_data: %s" % cleaned_data)
        return cleaned_data

class SoftDeleteRecordAdminForm(ModelForm):
    class Meta:
        model = SoftDeleteRecord
        readonly_fields = ('created', )
        exclude = ('content_type', 'object_id', 'changeset')

    def clean(self, *args, **kwargs):
        logging.info("in apikeyprofileform.clean")
        cleaned_data = super(SoftDeleteRecordAdminForm, self).clean(*args,
                                                                     **kwargs)
        if self.data.has_key('undelete'):
            logging.info("data has key:  undelete")
            self.instance.undelete()
            logging.info("undeleted!")
        return cleaned_data
