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
    """
    A record of a Braintree Customer. One to one relationship to a payer model.

    Calling the customer's related model "entity" helps remind us
    that we might not have a user object as the Payer Model.
    """
    entity = models.OneToOneField(
        getattr(settings, 'DJBRAINTREE_PAYER_MODEL', settings.AUTH_USER_MODEL),
        null=True)

    # objects = CustomerManager()
    def str_parts(self):
        return [
                   smart_text(self.entity),
                   "email={email}".format(email=self.entity.email),
               ] + super(Customer, self).str_parts()

    @classmethod
    def get_or_create(cls, entity, **kwargs):
        try:
            return Customer.objects.get(entity=entity), False
        except Customer.DoesNotExist:
            return cls.create(entity, **kwargs), True

    @classmethod
    def create(cls, entity, **kwargs):
        email = kwargs.pop('email', entity.email)
        result = cls.api().create(dict(
            email=email,
            **kwargs
        ))
        obj = cls.extract_object_from_result(result)
        data = cls.braintree_object_to_record(obj)
        customer = Customer.objects.create(entity=entity, **data)
        return customer

    def update(self, **kwargs):
        result = super(Customer, self).update(**kwargs)
        obj = self.extract_object_from_result(result)
        self.sync(obj)
        return self

    def sync(self, braintree_object=None):
        super(Customer, self).sync(braintree_object)
        self.save()

    def sync_transactions(self, braintree_collection=None, **kwargs):
        if braintree_collection is None:
            braintree_collection = self.retrieve_transactions()
        for transaction in braintree_collection.items:
            self.record_transaction(transaction)

    def record_transaction(self, braintree_transaction):
        return Transaction.sync_from_braintree_object(braintree_transaction)


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
    customer = models.ForeignKey(Customer,
                                 related_name="transactions",
                                 null=True)

    @classmethod
    def sync_from_braintree_object(cls, braintree_object):
        try:
            transaction = cls.braintree_objects.get_by_json(braintree_object.id)
        except cls.DoesNotExist:
            transaction = cls.create_from_braintree_object(braintree_object)
        else:
            transaction.sync(braintree_object)

        try:
            customer = cls.object_to_customer(Customer.braintree_objects,
                                              braintree_object)
        except Customer.DoesNotExist:
            customer = None
        transaction.customer = customer
        transaction.save()
        return transaction

    def sync(self, braintree_object=None):
        super(Transaction, self).sync(braintree_object)
        self.save()

    def capture(self, amount=None):
        result = super(Transaction, self).capture(amount)
        if result.is_success:
            self.sync(result.transaction)
        return result

    def refund(self, amount=None):
        """
        Refunds work by returning a new braintree.Transaction that refunds or
        partially refunds the initial braintree.Transaction.
        That means we can't use the returned transaction to sync the
        initial transaction, but should create a new Transaction related to it.

        :param amount: The amount to refund
        :type amount: decimal.Decimal
        :return: The transaction refunded plus the result which wraps the Tx
            that represents the refund action.
        :rtype: tuple[Transaction, Union[SuccessfulResult, ErrorResult]]
        """
        refunded_tx, result = super(Transaction, self).refund(amount)
        if result.is_success:
            refunded_tx.save()  # Has been sync()'ed, so will have new TX in refund_ids

            # Creates a new "refund transaction" which should have this
            # instance's `braintree_id` as `refunded_transaction_id`
            Transaction.sync_from_braintree_object(result.transaction)
        return (refunded_tx, result)


    def void(self):
        result = super(Transaction, self).void()
        if result.is_success:
            self.sync(result.transaction)
        return result

    def hold_in_escrow(self):
        result = super(Transaction, self).hold_in_escrow()
        if result.is_success:
            self.sync(result.transaction)
        return result

    def release_from_escrow(self):
        result = super(Transaction, self).release_from_escrow()
        if result.is_success:
            self.sync(result.transaction)
        return result

    def cancel_release(self):
        result = super(Transaction, self).cancel_release()
        if result.is_success:
            self.sync(result.transaction)
        return result


# Run with models.py
configure_braintree()
