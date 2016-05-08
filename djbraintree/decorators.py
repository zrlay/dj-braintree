# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import warnings
from functools import wraps

from django.utils.decorators import available_attrs
from django.shortcuts import redirect

from .utils import entity_has_active_subscription
from .settings import subscriber_request_callback


def entity_passes_pay_test(test_func, pay_page="djbraintree:subscribe"):
    """
    Decorator for views that checks that the subscriber passes the given test for a "Paid Feature",
    redirecting to the pay form if necessary. The test should be a callable
    that takes the payer object and returns True if the payer passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(subscriber_request_callback(request)):
                return view_func(request, *args, **kwargs)

            return redirect(pay_page)
        return _wrapped_view
    return decorator


def subscription_payment_required(function=None, pay_page="djbraintree:subscribe"):
    """
    Decorator for views that require subscription payment, redirecting to the
    subscribe page if necessary.
    """

    actual_decorator = entity_passes_pay_test(
        entity_has_active_subscription,
        pay_page=pay_page
    )
    if function:
        return actual_decorator(function)
    return actual_decorator
