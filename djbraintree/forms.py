# -*- coding: utf-8 -*-
"""
.. module:: djbraintree.forms
   :synopsis: dj-braintree Forms.

.. moduleauthor:: Daniel Greenfeld (@pydanny)

"""

from django import forms

from .settings import PLAN_CHOICES


class PlanForm(forms.Form):
    plan = forms.ChoiceField(choices=PLAN_CHOICES)


class CancelSubscriptionForm(forms.Form):
    pass
