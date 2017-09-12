django-softdelete

Soft delete for Django ORM, with support for undelete.

This project provides undelete of soft-deleted objects, along with proper undeletion of related objects.

Inspired by http://codespatter.com/2009/07/01/django-model-manager-soft-delete-how-to-customize-admin/

Requirements
============

* Django 1.8
* django.contrib.contenttypes

Configuration
=============

There are simple templates files in `templates/`.  You will need to add Django's
egg loader to use the templates as is:

    TEMPLATE_LOADERS = (
    ...
        'django.template.loaders.eggs.Loader',
    )

Add the project `softdelete` to your `INSTALLED_APPS` for
through-the-web undelete support.

    INSTALLED_APPS = (
    ...
        'django.contrib.contenttypes',
        'softdelete',
    )

How It Works
============

Central to the ability to undelete a soft-deleted model is the concept of changesets.  When you
soft-delete an object, any objects referencing it via a ForeignKey, ManyToManyField, or OneToOneField will
also be soft-deleted.  This mimics the traditional CASCADE behavior of a SQL DELETE.

When the soft-delete is performed, the system makes a ChangeSet object which tracks all affected objects of
this delete request.  Later, when an undelete is requested, this ChangeSet is referenced to do a cascading
undelete.

If you are undeleting an object that was part of a ChangeSet, that entire ChangeSet is undeleted.

Once undeleted, the ChangeSet object is removed from the underlying database with a regular ("hard") delete.

Testing
=======

Can be tested directly with the following command:

    django-admin.py test softdelete --settings="softdelete.settings"
