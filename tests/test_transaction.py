"""
.. module:: dj-braintree.tests.test_transaction
   :synopsis: dj-braintree Transaction Model Tests.

.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""

from datetime import timedelta
from decimal import Decimal

from django.test.testcases import TestCase
from django.utils import timezone

from mock import patch

from djbraintree.models import Transaction, Customer
from tests import convert_to_fake_success_result

FAKE_TRANSACTION = {
    "id": "ch_xxxxxxxxxxxx",
    "additional_processor_response": "",
    "amount": "9.95",
    "avs_error_response_code": "U",
    "avs_postal_code_response_code": "I",
    "avs_street_address_response_code": "I",
    "channel": "",
    "created_at": timezone.now(),
    "currency_iso_code": "USD",
    "cvv_response_code": "U",
    "customer_details" : {
      "email" : "customer@gmail.com",
        "id": "cus_xxxxxxxxxxxxxxx",
    },

    "descriptor": {
        "name": "",
        "phone": "",
        "url": "",
    },

    "disbursement_details": {
        "disbursement_date": None,
        "funds_held": "",
        "settlement_amount": None,
        "settlement_currency_exchange_rate": None,
        "settlement_currency_iso_code": "USD",
        "success": "",
    },

    "escrow_status": "",
    "gateway_rejection_reason": "",
    "merchant_account_id": "dj_merch_id",
    "order_id": "order_xxxxxxxx",
    "payment_instrument_type": "credit_card",

    "paypal_details": {
        "authorization_id": "",
        "capture_id": "",
        "payer_email": "",
        "payer_first_name": "",
        "payer_id": "",
        "payer_last_name": "",
        "payment_id": "",
        "refund_id": "",
        "seller_protection_status": "",
        "tax_id_type": "",
        "transaction_fee_amount": "",
        "transaction_fee_currency_iso_code": "",
        "token": "",
        "image_url": "",
    },

    "plan_id": "",
    "processor_authorization_code": "A",
    "processor_response_code": "100",
    "processor_response_text": "Good.",
    "processor_settlement_response_code": "",
    "processor_settlement_response_text": "",
    "purchase_order_number": "po_xxxxxxxx",
    "recurring": False,
    "refund_ids": "",
    "refunded_transaction_id": "",

    "risk_data": {
        "decision": "Not Evaluated",
        "id": "risk_xxxxxxxx",
    },

    "service_fee_amount": "1.00",
    "settlement_batch_id": "",
    "status": "authorized",
    "status_history": "",

    "subscription_details": {
        "billing_period_end_date": "",
        "billing_period_start_date": "",
    },

    "subscription_id": "",
    "tax_amount": "",
    "tax_exempt": False,

    "three_d_secure_info": {
        "enrolled": "U",
        "liability_shift_possible": False,
        "liability_shifted": False,
        "status": "yes",
    },

    "type": "sale",
    "updated_at": timezone.now(),
    "voice_referral_number": "",
}


class TransactionTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            braintree_id="cus_xxxxxxxxxxxxxxx")

    def test_str(self):
        transaction = Transaction(amount=50, status="Authorized",
                                  braintree_id='transaction_xxxxxxxxxxxxxx')
        self.assertEqual(
            "<amount=50, status=Authorized, braintree_id=transaction_xxxxxxxxxxxxxx>",
            str(transaction))

    def test_sync_from_braintree_data(self):
        from braintree.transaction import Transaction as BTTransaction
        result = convert_to_fake_success_result(BTTransaction,
                                                Transaction,
                                                FAKE_TRANSACTION)
        transaction = Transaction.sync_from_braintree_object(result.transaction)

        self.assertEqual(Decimal("9.95"), transaction.amount)
        self.assertEqual(None, transaction.amount_refunded)

    @patch("djbraintree.models.Site.objects.get_current")
    def test_send_receipt_not_sent(self, get_current_mock):
        transaction = Transaction(receipt_sent=True)
        transaction.send_receipt()

        # Assert the condition caused exit
        self.assertFalse(get_current_mock.called)
