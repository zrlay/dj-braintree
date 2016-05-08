# -*- coding: utf-8 -*-
"""
.. module:: djbraintree.context_processors
   :synopsis: dj-braintree Context Processors.

.. moduleauthor:: Daniel Greenfeld (@pydanny)
.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""

import warnings


def djbraintree_settings(request):
    warnings.warn("This context processor is deprecated. It will be removed in dj-braintree 1.0.", DeprecationWarning)
    return None
