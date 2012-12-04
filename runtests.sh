#!/bin/sh
DJANGO_SETTINGS_MODULE=test_settings django-admin.py test --pythonpath `pwd` --settings test_settings picklefield
