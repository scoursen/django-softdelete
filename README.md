# django-softdelete  [![Build Status](https://travis-ci.com/mark0978/django-softdelete.svg?branch=master)](https://travis-ci.com/mark0978/django-softdelete)

Soft delete for Django ORM, with support for undelete.  Supports Django 2.0+

This project provides undelete of soft-deleted objects, along with proper undeletion of related objects.

Inspired by http://codespatter.com/2009/07/01/django-model-manager-soft-delete-how-to-customize-admin/

## Requirements


* Django 1.8+
* django.contrib.contenttypes

## Installation

    pip install django-softdelete

## Configuration

There are simple templates files in `templates/`.  You will need to add Django's
egg loader to use the templates as is, that would look something like this:

    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': '/path/to/my/templates',
            'OPTIONS': {
                 'loaders': (
                      'django.template.loaders.filesystem.Loader',
                      'django.template.loaders.app_directories.Loader',
                  ),
             }
        },
    ]

Add the project `softdelete` to your `INSTALLED_APPS` for
through-the-web undelete support.

    INSTALLED_APPS = (
    ...
        'django.contrib.contenttypes',
        'softdelete',
    )

Usage
=====
- Run `django-admin migrate`
- For the models that you want __soft delete__ to be implemented in, inherit from the `SoftDeleteObject` with `from softdelete.models import SoftDeleteObject`. Something like `MyCustomModel(SoftDeleteObject, models.Model)`. This will add an extra `deleted_at` field which will appear in the admin form after deleting/undeleting the object
- If you have a custom manager also make sure to inherit from the `SoftDeleteManager`.
- After that you can test it by __deleting__ and __undeleting__ objects from your models. Have fun undeleting :)

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

## Testing


Can be tested directly with the following command:

    django-admin.py test softdelete --settings="softdelete.settings"
