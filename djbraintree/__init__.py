from __future__ import unicode_literals
import warnings

from django import get_version as get_django_version

__title__ = "dj-braintree"
__summary__ = "Django + Braintree Marketplace"
__uri__ = "https://github.com/mightbejosh/dj-braintree/"

__version__ = "0.1.0.dev"

__author__ = "Zach Layng"
__email__ = "mightbejosh@gmail.com"

__license__ = "BSD"
__license__ = "License :: OSI Approved :: BSD License"
__copyright__ = "Copyright 2016 Zach Layng"

if get_django_version() <= '1.7.x':
    msg = "dj-braintree deprecation notice: Django 1.7 and lower are not\n" \
        "supported. Please upgrade to Django 1.8 or higher.\n"
    warnings.warn(msg)
