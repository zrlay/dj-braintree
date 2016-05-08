# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings

from braintree.exceptions.not_found_error import NotFoundError

from .models import Customer


def sync_entity(entity):
    customer, created = Customer.get_or_create(entity=entity)
    try:
        braintree_customer_object = customer.api_find()
        customer.sync(braintree_customer_object)
        # customer.sync_current_subscription(cu=stripe_customer)
        # customer.sync_invoices(cu=stripe_customer)
        # customer.sync_charges(cu=stripe_customer)
    except NotFoundError as e:
        print("ERROR: " + str(e))
    return customer

#
# def sync_plans(api_key=settings.BRAINTREE_PRIVATE_KEY):
#     stripe.api_key = api_key
#     for plan in settings.DJSTRIPE_PLANS:
#         stripe_plan = settings.DJSTRIPE_PLANS[plan]
#         if stripe_plan.get("stripe_plan_id"):
#             try:
#                 stripe.Plan.create(
#                     amount=stripe_plan["price"],
#                     interval=stripe_plan["interval"],
#                     name=stripe_plan["name"],
#                     currency=stripe_plan["currency"],
#                     id=stripe_plan["stripe_plan_id"],
#                     interval_count=stripe_plan.get("interval_count"),
#                     trial_period_days=stripe_plan.get("trial_period_days"),
#                     statement_descriptor=stripe_plan.get("statement_descriptor"),
#                     metadata=stripe_plan.get("metadata")
#                 )
#                 print("Plan created for {0}".format(plan))
#             except Exception as e:
#                 print("ERROR: " + str(e))
