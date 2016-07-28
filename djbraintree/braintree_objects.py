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

from .utils import VERIFICATION_CHOICES, STATUS_CHOICES, THREE_D_SECURE_CHOICES

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
        Get the api object for this type of braintree object (requires
        braintree_api_name attribute to be set on model).
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
    def braintree_object_to_record(cls, braintree_object):
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
    def create_from_braintree_object(cls, braintree_object):
        """
        Create a model instance (not saved to db),
        using the given data object from Braintree.
        Since the braintree python sdk can return Resources that are
        entirely blank, we check if the resource has an `id` before creating.

        :type data: braintree.Resource
        """
        if braintree_object and braintree_object.id:
            return cls(**cls.braintree_object_to_record(braintree_object))
        return None

    @classmethod
    def extract_object_from_result(cls, result):
        """
        Extracts response object (data) from a successful result object
        """
        assert result.is_success
        return getattr(result, cls.braintree_api_name.lower())

    def sync(self, braintree_object=None):
        if not braintree_object:
            braintree_object = self.api_find()
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

    def delete(self, using=None, keep_parents=False):
        self.destroy()
        return super(BraintreeCustomer, self).delete(using=using,
                                                     keep_parents=keep_parents)

    def charge(self, amount, options=None, **kwargs):
        """
        This method expects `amount` to be a Decimal type representing a
        dollar amount.
        """
        if not isinstance(amount, Decimal):
            raise ValueError(
                "You must supply a decimal value representing dollars."
            )

        payment_method_token = kwargs.get('payment_method_token')
        payment_method_nonce = kwargs.get('payment_method_nonce')
        if not (payment_method_token or payment_method_nonce):
            raise ValueError(
                "You must supply a payment method nonce or token."
            )

        data = dict(
            amount=amount,
            customer_id=self.braintree_id,
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
            "company": obj.company or '',
            "created_at": obj.created_at or None,
            "email": obj.email or '',
            "fax": obj.fax or '',
            "first_name": obj.first_name or '',
            "last_name": obj.last_name or '',
            "phone": obj.phone or '',
            "updated_at": obj.updated_at or None,
            "website": obj.website or '',
        }
        return data

    def retrieve_transactions(self):
        collection = braintree.Transaction.search(
            braintree.TransactionSearch.customer_id == self.braintree_id
        )
        return collection


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
    # TODO: Refactor amount_refunded to query amounts on related refund Txs
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
                                            null=True)
    settlement_currency_exchange_rate = models.DecimalField(decimal_places=8,
                                                            null=True,
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

    @classmethod
    def braintree_object_to_record(cls, obj):

        data = {
            "braintree_id": obj.id,
            "additional_processor_response": obj.additional_processor_response or '',
            "amount": obj.amount,
            "avs_error_response_code": obj.avs_error_response_code or '',
            "avs_postal_code_response_code": obj.avs_postal_code_response_code or '',
            "avs_street_address_response_code": obj.avs_street_address_response_code or '',
            "channel": obj.channel or '',
            "created_at": obj.created_at,

            "currency_iso_code": obj.currency_iso_code or '',
            "cvv_response_code": obj.cvv_response_code,

            # Descriptor Fields
            "name": obj.descriptor.name or '',
            "phone": obj.descriptor.phone or '',
            "url": obj.descriptor.url or '',

            # Disbursement Details
            "disbursement_date": obj.disbursement_details.disbursement_date,
            "funds_held": obj.disbursement_details.funds_held or '',
            "settlement_amount": obj.disbursement_details.settlement_amount,
            "settlement_currency_exchange_rate": obj.disbursement_details.settlement_currency_exchange_rate,
            "settlement_currency_iso_code": obj.disbursement_details.settlement_currency_iso_code or '',
            "disbursement_success": obj.disbursement_details.success,

            "escrow_status": obj.escrow_status or '',
            "gateway_rejection_reason": obj.gateway_rejection_reason or '',
            "merchant_account_id": obj.merchant_account_id,
            "order_id": obj.order_id or '',
            "payment_instrument_type": obj.payment_instrument_type,

            "plan_id": obj.plan_id or '',
            "processor_authorization_code": obj.processor_authorization_code or '',
            "processor_response_code": obj.processor_response_code or '',
            "processor_response_text": obj.processor_response_text or '',
            "processor_settlement_response_code": obj.processor_settlement_response_code or '',
            "processor_settlement_response_text": obj.processor_settlement_response_text or '',
            "purchase_order_number": obj.purchase_order_number or '',
            "recurring": obj.recurring or '',
            "refund_ids": obj.refund_ids or '',
            "refunded_transaction_id": obj.refunded_transaction_id or '',

            "service_fee_amount": obj.service_fee_amount,
            "settlement_batch_id": obj.settlement_batch_id or '',
            "status": obj.status,
            "status_history": obj.status_history or '',

            "billing_period_end_date": obj.subscription_details.billing_period_end_date,
            "billing_period_start_date": obj.subscription_details.billing_period_start_date,

            "subscription_id": obj.subscription_id or '',
            "tax_amount": obj.tax_amount,
            "tax_exempt": obj.tax_exempt,

            "transaction_type": obj.type,
            "updated_at": obj.updated_at,
            "voice_referral_number": obj.voice_referral_number or '',
        }

        if obj.payment_instrument_type == braintree.PaymentInstrumentType.PayPalAccount:
            paypal_fields = {
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
            }

            for field in paypal_fields:
                if not paypal_fields[field]:
                    paypal_fields[field] = ''

            data.update(paypal_fields)
        else:
            payment_fields = {
                "token": obj.credit_card_details.token or '',
                "image_url": obj.credit_card_details.image_url,
            }
            data.update(payment_fields)

        # Fragile Fields
        # Some returned dicts seem to return as None instead of empty objects.
        if obj.risk_data:
            data.update({
                "decision": obj.risk_data.decision,
                "risk_data_id": obj.risk_data.id,
            })
        if obj.three_d_secure_info:
            data.update({
                "enrolled": obj.three_d_secure_info.enrolled,
                "liability_shift_possible": obj.three_d_secure_info.liability_shift_possible,
                "liability_shifted": obj.three_d_secure_info.liability_shifted,
                "three_d_secure_status": obj.three_d_secure_info.status,
            })

        for field in data:
            if field.endswith("amount") and data[field]:
                try:
                    data[field] = Decimal(data[field]).quantize(Decimal('.01'))
                except TypeError:
                    data[field] = None

            if field.endswith("date") or field.endswith("_at"):
                if not data[field]:
                    data[field] = None

        return data

    def capture(self, amount=None):
        if amount and amount < self.amount:
            amount = Decimal(amount).quantize(Decimal('.01'))
            result = self.api().submit_for_settlement(
                self.braintree_id, amount)
        else:
            result = self.api().submit_for_settlement(
                self.braintree_id) # Defaults to full capture.

        return result

    def void(self):
        result = self.api().void(self.braintree_id)
        return result

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
        """
        Refunds work by returning a new braintree.Transaction that refunds or
        partially refunds the initial braintree.Transaction.
        That means we can't use the returned transaction to overwrite the
        initial transaction, but should create a new Transaction related to it.

        :param amount: The amount to refund
        :type amount: decimal.Decimal
        :return: The transaction refunded plus the result which wraps the Tx
            that represents the refund action.
        :rtype: tuple[Transaction, Union[SuccessfulResult, ErrorResult]]
        """
        max_amount = self.calculate_max_refund(amount=amount)
        if amount:
            result = self.api().refund(self.braintree_id,
                                       max_amount)
        else:
            result = self.api().refund(self.braintree_id)

        if result.is_success:
            self.sync()  # Will fetch new refund_ids for this instance.
            self.amount_refunded = max_amount + (self.amount_refunded or 0)
        return (self, result)

    def clone(self):
        raise NotImplementedError(
            "From Braintree docs: Instead of cloning transactions, "
            "a better practice in most cases is to use the Vault to save "
            "and reuse payment method or customer information.")

    def hold_in_escrow(self):
        result = self.api().hold_in_escrow(self.braintree_id)
        return result

    def release_from_escrow(self):
        result = self.api().release_from_escrow(self.braintree_id)
        return result

    def cancel_release(self):
        result = self.api().cancel_release(self.braintree_id)
        return result

    @classmethod
    def object_to_customer(cls, manager, braintree_object):
        """
        Search the given manager for the customer matching this
        BraintreeTransaction object.

        :param manager: braintree_objects manager for a table
            of BraintreeCustomers
        :type manager: BraintreeObjectManager
        :param braintree_object: Object returned from API
        :type braintree_object: braintree.Transaction
        :return: The Customer linked to this transaction, if any
        :rtype: Optional[Customer]
        """
        customer_object = cls.object_to_customer_object(braintree_object)
        if customer_object:
            return manager.get_by_resource(customer_object)
        return None

    @classmethod
    def object_to_customer_object(cls, braintree_object):
        """
        Extracts the braintree.Customer from a braintree.Transaction

        :param braintree_object: The braintree.Transaction containing
            customer details.
        :return: The customer resource object
        :rtype: Optional[braintree.Customer]
        """
        if braintree_object.customer_details.id:
            return braintree_object.customer_details
        return None

    @classmethod
    def object_to_merchant_account(cls, manager, braintree_object):
        """
        Search the given manager for the merchant account matching this
        BraintreeTransaction object.

        :param manager: braintree_objects manager for a
        table of BraintreeMerchantAccount
        :type manager: BraintreeObjectManager
        :param braintree_object: Object returned from API
        :type braintree_object: braintree.Transaction
        """
        if getattr(braintree_object, "merchant_account_id"):
            return manager.get_by_resource(braintree_object.merchant_account_id)
        return None
