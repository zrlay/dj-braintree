"""
.. module:: dj-braintree.tests.test_transaction
   :synopsis: dj-braintree Transaction Model Tests.

.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""
from decimal import Decimal

import decimal

from django.contrib.auth import get_user_model
from django.test.testcases import TestCase

from mock import patch

from djbraintree.models import Transaction, Customer
from tests import convert_to_fake_success_result, FAKE_TRANSACTION


class TransactionTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="patrick",
                                                         email="patrick@gmail.com")
        self.customer = Customer.objects.create(
            entity=self.user,
            braintree_id="cus_xxxxxxxxxxxxxxx",
        )

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

    @patch("braintree.Transaction.refund")
    @patch("braintree.Transaction.find")
    def test_refund_transaction(self, transaction_refund_mock,
                                transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "tx_XXXXXX",
            "amount": "10.00",
            "captured": True,
            "amount_refunded": "10.00",
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction.refund()
        transaction2 = Transaction.objects.get(braintree_id="ch_XXXXXX")
        self.assertEquals(transaction2.refunded, True)
        self.assertEquals(transaction2.amount_refunded,
                          decimal.Decimal("10.00"))

    @patch("braintree.Transaction.refund")
    @patch("braintree.Transaction.find")
    def test_refund_transaction_passes_extra_args(self, transaction_refund_mock,
                                                  transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "tx_XXXXXX",
            "amount": "10.00",
            "captured": True,
            "amount_refunded": "10.00",
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction.refund(
            amount=decimal.Decimal("10.00"),
        )
        kwargs = transaction_retrieve_mock.return_value.refund.call_args
        self.assertEquals(kwargs["reverse_transfer"], True)
        self.assertEquals(kwargs["refund_application_fee"], False)

    @patch("braintree.Transaction.submit_for_settlement")
    def test_capture_transaction(self, transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "tx_XXXXXX",
            "amount": "10.00",
            "captured": True,
            "amount_refunded": "10.00",
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction2 = transaction.capture()
        self.assertEquals(transaction2.captured, True)

    @patch("braintree.Transaction.refund")
    def test_refund_transaction_object_returned(self,
                                                transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "tx_XXXXXX",
            "amount": "10.00",
            "captured": True,
            "amount_refunded": "10.00",
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction2 = transaction.refund()
        self.assertEquals(transaction2.refunded, True)
        self.assertEquals(transaction2.amount_refunded,
                          decimal.Decimal("10.00"))

    def test_calculate_refund_amount_full_refund(self):
        transaction = Transaction(
            braintree_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_max_refund(),
            500
        )

    def test_calculate_refund_amount_partial_refund(self):
        transaction = Transaction(
            braintree_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_max_refund(
                amount=decimal.Decimal("300.00")),
            300
        )

    def test_calculate_refund_above_max_refund(self):
        transaction = Transaction(
            braintree_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_max_refund(
                amount=decimal.Decimal("600.00")),
            500
        )

