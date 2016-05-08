# -*- coding: utf-8 -*-
"""
.. module:: dj-braintree.mixins
   :synopsis: dj-braintree Mixins.

.. moduleauthor:: Daniel Greenfield (@pydanny)

"""

from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect

from . import settings as djbraintree_settings
from .models import Customer, CurrentSubscription
from .utils import subscriber_has_active_subscription


class SubscriptionPaymentRequiredMixin(object):
    """
    Checks if the subscriber has an active subscription. If not, redirect to
    the subscription page.
    """

    def dispatch(self, request, *args, **kwargs):
        if not subscriber_has_active_subscription(djbraintree_settings.subscriber_request_callback(request)):
            message = "Your account is inactive. Please renew your subscription"
            messages.info(request, message, fail_silently=True)
            return redirect("djbraintree:subscribe")

        return super(SubscriptionPaymentRequiredMixin, self).dispatch(request, *args, **kwargs)


class PaymentsContextMixin(object):
    """Adds plan context to a view."""

    def get_context_data(self, **kwargs):
        context = super(PaymentsContextMixin, self).get_context_data(**kwargs)
        context.update({
            "BRAINTREE_PUBLIC_KEY": settings.BRAINTREE_PUBLIC_KEY,
            "PLAN_CHOICES": djbraintree_settings.PLAN_CHOICES,
            "PLAN_LIST": djbraintree_settings.PLAN_LIST,
            "PAYMENT_PLANS": djbraintree_settings.PAYMENTS_PLANS
        })
        return context


class SubscriptionMixin(PaymentsContextMixin):
    """Adds customer subscription context to a view."""

    def get_context_data(self, *args, **kwargs):
        context = super(SubscriptionMixin, self).get_context_data(**kwargs)
        context['is_plans_plural'] = bool(len(djbraintree_settings.PLAN_CHOICES) > 1)
        context['customer'], created = Customer.get_or_create(
            subscriber=djbraintree_settings.subscriber_request_callback(self.request))
        context['CurrentSubscription'] = CurrentSubscription
        return context
