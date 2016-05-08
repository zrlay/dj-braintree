# -*- coding: utf-8 -*-
"""
.. module:: django-braintree-marketplace.braintree_objects
   :synopsis: django-braintree-marketplace - Abstract model definitions to
   provide our view of Braintree's objects


This module is an effort to isolate (as much as possible)
the API dependent code in one place. Primarily this is:

1) create models containing the fields that we care about,
mapping to Braintree's fields
2) create methods for consistently syncing our database with
Braintree's version of the objects
3) centralized routines for creating new database records to
match incoming Braintree objects

This module defines abstract models which are then extended in models.py
to provide the remaining django-braintree-marketplace functionality.
"""

import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible

from model_utils.models import TimeStampedModel
import braintree

from .managers import BraintreeObjectManager

from django_braintree_marketplace.utils import VERIFICATION_CHOICES, \
    STATUS_CHOICES, THREE_D_SECURE_CHOICES

public_key = settings.BRAINTREE_PUBLIC_KEY
private_key = settings.BRAINTREE_PRIVATE_KEY
merchant_id = settings.BRAINTREE_MERCHANT_ID
environment = getattr(settings, "BRAINTREE_ENVIRONMENT", "sandbox")


def configure_braintree():
    braintree.Configuration.configure(braintree.Environment.All[environment],
                                      merchant_id=merchant_id,
                                      public_key=public_key,
                                      private_key=private_key)

@python_2_unicode_compatible
class BraintreeObject(TimeStampedModel):
    # This must be defined in descendants of this model/mixin
    # e.g. "Address", "Transaction", "Customer", etc.
    braintree_api_name = None
    objects = models.Manager()
    braintree_objects = BraintreeObjectManager()

    class Meta:
        abstract = True

    braintree_id = models.CharField(max_length=50, unique=True)

    @classmethod
    def api(cls):
        """
        Get the api object for this type of stripe object (requires
        stripe_api_name attribute to be set on model).
        """
        if cls.braintree_api_name is None:
            raise NotImplementedError(
                "BraintreeObject descendants are required to define "
                "the braintree_api_name attribute")
        # e.g. braintree.Customer, braintree.Transaction, etc
        return getattr(braintree, cls.braintree_api_name)

    def api_find(self):
        """
        Implement very commonly used API function 'find'
        """
        # Run braintree.X.find(id)
        return type(self).api().find(self.braintree_id)

    def str_parts(self):
        """
        Extend this to add information to the objects' string representation

        :rtype: list of str
        """
        return ["braintree_id={id}".format(id=self.braintree_id)]

    @classmethod
    def braintree_object_to_record(cls, data):
        """
        This takes a Result object, as it is formatted in
        Braintree's current API for our object type.
        In return, it provides a dict.
        The dict can be used to create a record or to update a record.

        This function takes care of mapping from one field name to another,
        eliminating unused fields (so that an objects.create()
        call would not fail).

        :param data: the object, as sent by Braintree.
        Parsed from JSON, into a dict
        :type data: dict
        :return: All the members from the input, translated, mutated, etc
        :rtype: dict
        """
        raise NotImplementedError()

    @classmethod
    def create_from_braintree_object(cls, data):
        """
        Create a model instance (not saved to db),
        using the given data object from Braintree.
        :type data: dict
        """
        return cls(**cls.braintree_object_to_record(data))

    @classmethod
    def extract_object_from_result(cls, result):
        """
        Extracts response object (data) form a successful result object
        """
        assert (result.is_success)
        return result.getattr(cls.braintree_api_name)

    def sync(self, braintree_object=None):
        data = self.braintree_object_to_record(braintree_object)
        for attr, value in data.items():
            setattr(self, attr, value)

    def __str__(self):
        return "<{list}>".format(list=", ".join(self.str_parts()))


class BraintreeCustomer(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "Customer"

    company = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(null=True)
    # TODO: custom fields
    email = models.EmailField(blank=True)
    fax = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=255, blank=True)
    last_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=14, blank=True)
    updated_at = models.DateTimeField(null=True)
    website = models.URLField(max_length=255, blank=True)

    @property
    def braintree_customer(self):
        return self.api_find()

    def has_default_payment_method(self):
        return braintree.PaymentMethod.find()

    def destroy(self):
        return self.api().delete(self.braintree_id)

    def charge(self, amount, options=None, **kwargs):
        """
        This method expects `amount` to be a Decimal type representing a
        dollar amount.
        """
        if not isinstance(amount, Decimal):
            raise ValueError(
                "You must supply a decimal value representing dollars."
            )

        data = dict(
            amount=amount,
            customer_id=self.customer_id,
            **kwargs
        )

        if options:
            if not isinstance(options, dict):
                raise ValueError(
                    "Options must be a dictionary"
                )
            data.update({"options": options})

        result = BraintreeTransaction.api().sale(data)
        return result

    def update(self, **kwargs):
        result = self.api().update(self.braintree_id, kwargs)
        return result

    @classmethod
    def braintree_object_to_record(cls, obj):
        data = {
            "braintree_id": obj.id,
            "company": obj.company,
            "created_at": obj.created_at,
            "email": obj.email,
            "fax": obj.fax,
            "first_name": obj.first_name,
            "last_name": obj.last_name,
            "phone": obj.phone,
            "updated_at": obj.updated_at,
            "website": obj.website,
        }
        return data

    def sync(self, data=None):
        super(BraintreeCustomer, self).sync(data)


class BraintreeAddress(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "Address"


class BraintreePaymentMethod(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "PaymentMethod"

    # The following fields are nested in the "credit_card_details" object
    card_bin = models.CharField(max_length=6, blank=True)
    card_type = models.CharField(max_length=100, blank=True)
    cardholder_name = models.CharField(max_length=255, blank=True)
    commercial = models.CharField(max_length=10, blank=True)
    country_of_issuance = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    customer_id = models.CharField(max_length=50, blank=True)
    customer_location = models.CharField(
        max_length=13,
        blank=True,
        choices=(
            ('US', 'US or Unspecified'), ('International', 'International'))
    )
    debit = models.CharField(max_length=10, blank=True)
    default = models.NullBooleanField(null=True)
    durbin_regulated = models.CharField(max_length=10, blank=True)
    expiration_date = models.CharField(max_length=6, blank=True)
    expiration_month = models.CharField(max_length=2, blank=True)
    expiration_year = models.CharField(max_length=4, blank=True)

    expired = models.BooleanField(default=False)

    healthcare = models.CharField(max_length=10, blank=True)
    image_url = models.URLField(null=True, blank=True)
    issuing_bank = models.TextField(blank=True)
    last_4 = models.CharField(max_length=4, blank=True)
    masked_number = models.CharField(max_length=16, blank=True)
    payroll = models.CharField(max_length=10, blank=True)
    prepaid = models.CharField(max_length=10, blank=True)
    # TODO: Subscriptions
    token = models.CharField(max_length=80, blank=True)
    unique_number_identifier = models.CharField(max_length=140, blank=True)
    updated_at = models.DateTimeField(null=True)

    @classmethod
    def braintree_object_to_record(cls, obj):
        data = {
            "card_bin": obj.bin,
            "card_type": obj.card_type,
            "cardholder_name": obj.cardholder_name,
            "commercial": obj.commercial,
            "country_of_issuance": obj.country_of_issuance,
            "customer_location": obj.customer_location,
            "debit": obj.debit,
            "durbin_regulated": obj.durbin_regulated,
            "expiration_date": obj.expiration_date,
            "healthcare": obj.healthcare,
            "image_url": obj.image_url,
            "issuing_bank": obj.issuing_bank,
            "last_4": obj.last_4,
            "masked_number": obj.masked_number,
            "payroll": obj.payroll,
            "prepaid": obj.prepaid,
            "token": obj.token,
            "unique_number_identifier": obj.unique_number_identifier,
        }
        return data


class BraintreeMerchantAccount(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "MerchantAccount"


class BraintreePlan(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "Plan"


class BraintreeSubscription(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "Subscription"


class BraintreeTransaction(BraintreeObject):
    class Meta:
        abstract = True

    braintree_api_name = "Transaction"

    additional_processor_response = models.CharField(max_length=255, blank=True)
    amount = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    amount_refunded = models.DecimalField(decimal_places=2, max_digits=7,
                                          null=True)
    avs_error_response_code = models.CharField(max_length=50, blank=True)
    avs_postal_code_response_code = models.CharField(
        max_length=1, blank=True,
        choices=VERIFICATION_CHOICES)
    avs_street_address_response_code = models.CharField(
        max_length=1, blank=True,
        choices=VERIFICATION_CHOICES)
    channel = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(blank=True, null=True)
    currency_iso_code = models.CharField(max_length=3, blank=True)
    cvv_response_code = models.CharField(max_length=1, blank=True,
                                         choices=VERIFICATION_CHOICES)
    # Descriptor Fields
    name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    url = models.URLField(null=True, blank=True)

    # Disbursement Details
    disbursement_date = models.DateTimeField(null=True, blank=True)
    funds_held = models.CharField(max_length=200, blank=True)
    settlement_amount = models.DecimalField(decimal_places=2, max_digits=7,
                                            blank=True)
    settlement_currency_exchange_rate = models.DecimalField(decimal_places=8,
                                                            blank=True,
                                                            max_digits=12)
    settlement_currency_iso_code = models.CharField(max_length=3, blank=True)
    disbursement_success = models.NullBooleanField(null=True, blank=True)

    # TODO: Discounts
    # TODO: Disputes

    escrow_status = models.CharField(
        max_length=40, blank=True,
        choices=[
            ("hold_pending", "hold_pending"),
            ("held", "held"),
            ("release_pending", "release_pending"),
            ("released", "released"),
            ("refunded", "refunded"),
        ])

    gateway_rejection_reason = models.CharField(
        max_length=60, blank=True,
        choices=[
            ("avs", "avs"),
            ("avs_and_cvv", "avs_and_cvv"),
            ("cvv", "cvv"),
            ("duplicate", "duplicate"),
            ("fraud", "fraud"),
            ("three_d_secure", "three_d_secure"),
            ("application_incomplete", "application_incomplete"),
        ])

    merchant_account_id = models.CharField(max_length=50, blank=True)
    order_id = models.CharField(max_length=200, blank=True)
    payment_instrument_type = models.CharField(max_length=100, blank=True)

    # Paypal
    authorization_id = models.CharField(max_length=200, blank=True)
    capture_id = models.CharField(max_length=200, blank=True)
    payer_email = models.CharField(max_length=200, blank=True)
    payer_first_name = models.CharField(max_length=200, blank=True)
    payer_id = models.CharField(max_length=200, blank=True)
    payer_last_name = models.CharField(max_length=200, blank=True)
    payment_id = models.CharField(max_length=200, blank=True)
    refund_id = models.CharField(max_length=200, blank=True)
    seller_protection_status = models.CharField(max_length=200, blank=True)
    tax_id_type = models.CharField(max_length=200, blank=True)
    transaction_fee_amount = models.DecimalField(decimal_places=2, max_digits=7,
                                                 null=True)
    transaction_fee_currency_iso_code = models.CharField(max_length=200,
                                                         blank=True)

    plan_id = models.CharField(max_length=255, blank=True)
    processor_authorization_code = models.CharField(max_length=100, blank=True)
    processor_response_code = models.CharField(max_length=40, blank=True)
    processor_response_text = models.CharField(max_length=255, blank=True)
    processor_settlement_response_code = models.CharField(max_length=40,
                                                          blank=True)
    processor_settlement_response_text = models.CharField(max_length=255,
                                                          blank=True)

    purchase_order_number = models.CharField(max_length=54, blank=True)
    recurring = models.NullBooleanField(null=True, blank=True)
    refund_ids = models.TextField(blank=True)
    refunded_transaction_id = models.CharField(max_length=40, blank=True)

    # Risk Data
    decision = models.CharField(max_length=40, blank=True)
    risk_data_id = models.CharField(max_length=200, blank=True)

    service_fee_amount = models.DecimalField(decimal_places=2, max_digits=7,
                                             null=True)
    settlement_batch_id = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=100, blank=True,
                              choices=STATUS_CHOICES)
    status_history = models.CharField(max_length=255, blank=True)

    # Subscription Details
    billing_period_end_date = models.DateTimeField(null=True)
    billing_period_start_date = models.DateTimeField(null=True)

    subscription_id = models.CharField(max_length=200, blank=True)

    tax_amount = models.DecimalField(decimal_places=2, max_digits=7, null=True)
    tax_exempt = models.NullBooleanField(null=True)

    # three_d_secure_info
    enrolled = models.CharField(max_length=1, blank=True,
                                choices=THREE_D_SECURE_CHOICES)
    liability_shift_possible = models.NullBooleanField(null=True)
    liability_shifted = models.NullBooleanField(null=True)
    three_d_secure_status = models.CharField(max_length=200, blank=True)

    transaction_type = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(null=True)
    voice_referral_number = models.CharField(max_length=200, blank=True)

    # TODO: Check if redundant w/ paypal
    image_url = models.URLField(null=True, blank=True)
    token = models.CharField(max_length=80, blank=True)

    def str_parts(self):
        return [
                   "amount={amount}".format(amount=self.amount),
                   "status={status}".format(status=self.status),
               ] + super(BraintreeTransaction, self).str_parts()

    def update_status(self):
        self.status = self.api_find().status
        self.save()

    @classmethod
    def braintree_object_to_record(cls, obj):

        data = {
            "braintree_id": obj.id,
            "additional_processor_response": obj.additional_processor_response,
            "amount": obj.amount,
            "avs_error_response_code": obj.avs_error_response_code,
            "avs_postal_code_response_code": obj.avs_postal_code_response_code,
            "avs_street_address_response_code": obj.avs_street_address_response_code,
            "channel": obj.channel,
            "created_at": obj.created_at,

            "currency_iso_code": obj.currency_iso_code,
            "cvv_response_code": obj.cvv_response_code,
            # Descriptor Fields
            "name": obj.descriptor.name,
            "phone": obj.descriptor.phone,
            "url": obj.descriptor.url,

            # Disbursement Details
            "disbursement_date": obj.disbursement_details.disbursement_date,
            "funds_held": obj.disbursement_details.funds_held,
            "settlement_amount": obj.disbursement_details.settlement_amount,
            "settlement_currency_exchange_rate": obj.disbursement_details.settlement_currency_exchange_rate,
            "settlement_currency_iso_code": obj.disbursement_details.settlement_currency_iso_code,
            "disbursement_success": obj.disbursement_details.success,

            "escrow_status": obj.escrow_status,
            "gateway_rejection_reason": obj.gateway_rejection_reason,
            "merchant_account_id": obj.merchant_account_id,
            "order_id": obj.order_id,
            "payment_instrument_type": obj.payment_instrument_type,

            # Paypal
            "authorization_id": obj.paypal_details.authorization_id,
            "capture_id": obj.paypal_details.capture_id,
            "payer_email": obj.paypal_details.payer_email,
            "payer_first_name": obj.paypal_details.payer_first_name,
            "payer_id": obj.paypal_details.payer_id,
            "payer_last_name": obj.paypal_details.payer_last_name,
            "payment_id": obj.paypal_details.payment_id,
            "refund_id": obj.paypal_details.refund_id,
            "seller_protection_status": obj.paypal_details.seller_protection_status,
            "tax_id_type": obj.paypal_details.tax_id_type,
            "transaction_fee_amount": obj.paypal_details.transaction_fee_amount,
            "transaction_fee_currency_iso_code": obj.paypal_details.transaction_fee_currency_iso_code,
            "token": obj.paypal_details.token,
            "image_url": obj.paypal_details.image_url,

            "plan_id": obj.plan_id,
            "processor_authorization_code": obj.processor_authorization_code,
            "processor_response_code": obj.processor_response_code,
            "processor_response_text": obj.processor_response_text,
            "processor_settlement_response_code": obj.processor_settlement_response_code,
            "processor_settlement_response_text": obj.processor_settlement_response_text,
            "purchase_order_number": obj.purchase_order_number,
            "recurring": obj.recurring,
            "refund_ids": obj.refund_ids,
            "refunded_transaction_id": obj.refunded_transaction_id,

            "decision": obj.risk_data.decision,
            "risk_data_id": obj.risk_data.id,

            "service_fee_amount": obj.service_fee_amount,
            "settlement_batch_id": obj.settlement_batch_id,
            "status": obj.status,
            "status_history": obj.status_history,

            "billing_period_end_date": obj.subscription_details.billing_period_end_date,
            "billing_period_start_date": obj.subscription_details.billing_period_start_date,

            "subscription_id": obj.subscription_id,
            "tax_amount": obj.tax_amount,
            "tax_exempt": obj.tax_exempt,

            "enrolled": obj.three_d_secure_info.enrolled,
            "liability_shift_possible": obj.three_d_secure_info.liability_shift_possible,
            "liability_shifted": obj.three_d_secure_info.liability_shifted,
            "three_d_secure_status": obj.three_d_secure_info.status,

            "transaction_type": obj.type,
            "updated_at": obj.updated_at,
            "voice_referral_number": obj.voice_referral_number,
            # "date": convert_tstamp(data, "date"),
        }
        for field in data:
            if field.endswith("amount"):
                data[field] = Decimal(data[field]).quantize(Decimal('.01'))

        return data

    def capture(self, amount=None):
        if amount:
            amount = Decimal(amount).quantize(Decimal('.01'))
            result = self.api().submit_for_settlement(
                self.braintree_id, amount)
        else:
            result = self.api().submit_for_settlement(
                self.braintree_id)

        return self._parse_result(result)

    def void(self):
        result = self.api().void(self.braintree_id)
        return self._parse_result(result)

    def calculate_max_refund(self, amount=None):
        """
        Tries to determine the max refund amount
        :rtype: int
        :return: amount that can be refunded

        """
        eligible_to_refund = self.amount - (self.amount_refunded or 0)
        if amount:
            amount_to_refund = min(eligible_to_refund, amount)
        else:
            amount_to_refund = eligible_to_refund
        return Decimal(amount_to_refund).quantize(Decimal('.01'))

    def refund(self, amount=None):
        max_amount = self.calculate_max_refund(amount=amount)
        if amount:
            result = self.api().refund(self.transaction_id,
                                       max_amount)
        else:
            result = self.api().refund(self.transaction_id)

        if result.is_success:
            self.amount_refunded += max_amount
            self.save()

        return self._parse_result(result)

    def clone(self):
        raise NotImplementedError(
            "From Braintree docs: Instead of cloning transactions, "
            "a better practice in most cases is to use the Vault to save "
            "and reuse payment method or customer information.")

    def hold_in_escrow(self):
        result = self.api().hold_in_escrow(self.braintree_id)
        return self._parse_result(result)

    def release_from_escrow(self):
        result = self.api().release_from_escrow(self.braintree_id)
        return self._parse_result(result)

    def cancel_release(self):
        result = self.api().cancel_release(self.braintree_id)
        return self._parse_result(result)

    @classmethod
    def object_to_customer(cls, manager, data):
        """
        Search the given manager for the customer matching this
        BraintreeTransaction object.

        :param manager: braintree_objects manager for a table
        of BraintreeCustomers
        :type manager: BraintreeObjectManager
        :param data: braintree object
        :type data: dict
        """
        return manager.get_by_json(data,
                                   "customer") if "customer" in data else None

    @classmethod
    def object_to_merchant_account(cls, manager, data):
        """
        Search the given manager for the merchant account matching this
        BraintreeTransaction object.

        :param manager: braintree_objects manager for a
        table of BraintreeMerchantAccount
        :type manager: BraintreeObjectManager
        :param data: braintree object
        :type data: dict
        """
        if "merchant_account" in data:
            return manager.get_by_json(data, "merchant_account")
        return None