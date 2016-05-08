# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import models

# Create your models here.
from django.utils.encoding import smart_text

from .braintree_objects import (BraintreeCustomer, BraintreeTransaction,
                                BraintreePaymentMethod, BraintreeSubscription,
                                BraintreePlan,
                                BraintreeMerchantAccount, BraintreeAddress,
                                configure_braintree)


class Customer(BraintreeCustomer):
    user = models.OneToOneField(
        getattr(settings, 'BRAINTREE_CUSTOMER_MODEL', settings.AUTH_USER_MODEL),
        null=True)

    # objects = CustomerManager()
    def str_parts(self):
        return [
                   smart_text(self.user),
                   "email={email}".format(email=self.user.email),
               ] + super(Customer, self).str_parts()

    @classmethod
    def get_or_create(cls, user, **kwargs):
        try:
            return Customer.objects.get(user=user), False
        except Customer.DoesNotExist:
            return cls.create(user, **kwargs), True

    @classmethod
    def create(cls, user, **kwargs):
        first_name = kwargs.pop('first_name', user.first_name)
        last_name = kwargs.pop('last_name', user.last_name)
        email = kwargs.pop('email', user.email)
        result = cls.api().create(dict(
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        ))
        obj = cls.extract_object_from_result(result)
        data = cls.braintree_object_to_record(obj)
        customer = Customer.objects.create(user=user, **data)
        return customer

    def update(self, **kwargs):
        result = super(Customer, self).update(**kwargs)
        obj = self.extract_object_from_result(result)
        self.sync(obj)
        return self

#
# class Address(BraintreeAddress):
#     customer = models.ForeignKey(Customer, related_name="addresses")
#
#
# class PaymentMethod(BraintreePaymentMethod):
#     pass
#
#
# class MerchantAccount(BraintreeMerchantAccount):
#     pass
#
#
# class Plan(BraintreePlan):
#     pass
#
#
# class Subscription(BraintreeSubscription):
#     pass


class Transaction(BraintreeTransaction):
    customer = models.ForeignKey(Customer, related_name="transactions")


# Run with models.py
configure_braintree()