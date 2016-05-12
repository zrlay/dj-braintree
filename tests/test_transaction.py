"""
.. module:: dj-braintree.tests.test_transaction
   :synopsis: dj-braintree Transaction Model Tests.

.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""
from decimal import Decimal

import decimal

from django.contrib.auth import get_user_model
from django.test.testcases import TestCase

from tests import get_fake_success_transaction

from mock import patch

from djbraintree.models import Transaction, Customer


class TransactionTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="patrick",
            email="patrick@gmail.com")
        self.customer = Customer.objects.create(
            entity=self.user,
            braintree_id="cus_xxxxxxxxxxxxxxx",
        )

    def test_str(self):
        transaction = Transaction(amount=50, status="Authorized",
                                  braintree_id='transaction_xxxxxxxxxxxxxx')
        self.assertEqual(
            "<amount=50, status=Authorized, "
            "braintree_id=transaction_xxxxxxxxxxxxxx>",
            str(transaction))

    def test_sync_from_braintree_object(self):
        result = get_fake_success_transaction()
        transaction = Transaction.sync_from_braintree_object(result.transaction)

        self.assertEqual(Decimal("10.00"), transaction.amount)
        self.assertIsNone(transaction.amount_refunded)

    @patch("braintree.Transaction.submit_for_settlement")
    def test_capture_transaction(self, transaction_settlement_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_settlement_mock.return_value = get_fake_success_transaction(
            status='submitted_for_settlement'
        )
        transaction.capture()
        self.assertEquals(transaction.status, "submitted_for_settlement")

    @patch("braintree.Transaction.refund")
    @patch("braintree.Transaction.find")
    def test_refund_transaction(self, transaction_find_mock,
                                transaction_refund_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_find_mock.return_value = get_fake_success_transaction(
            id='tx_XXXXXX').transaction
        transaction_refund_mock.return_value = get_fake_success_transaction(
            type='credit')
        transaction.refund()
        transaction1 = Transaction.objects.get(braintree_id="tx_XXXXXX")
        transaction2 = Transaction.objects.get(braintree_id="d5y99n")
        self.assertEquals(transaction1.amount_refunded,
                          decimal.Decimal("10.00"))
        self.assertEquals(transaction1.transaction_type, "sale")
        self.assertEquals(transaction2.amount, decimal.Decimal("10.00"))
        self.assertEquals(transaction2.transaction_type, "credit")

    @patch("braintree.Transaction.refund")
    @patch("braintree.Transaction.find")
    def test_refund_transaction_passes_extra_args(self, transaction_find_mock,
                                                  transaction_refund_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            customer=self.customer,
            amount=decimal.Decimal("10.00"),
        )
        transaction_find_mock.return_value = get_fake_success_transaction(
            id='tx_XXXXXX').transaction
        transaction_refund_mock.return_value = get_fake_success_transaction(
            type='credit')
        transaction.refund(
            amount=decimal.Decimal("8.00"),
        )
        self.assertEquals(transaction.amount_refunded, Decimal("8.00"))
        self.assertEquals(Transaction.objects.count(), 2)

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

    @patch("braintree.Transaction.void")
    def test_void(self, transaction_void_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            amount=decimal.Decimal("10.00"),
        )
        transaction_void_mock.return_value = get_fake_success_transaction(
            status='voided'
        )
        transaction.void()
        self.assertEquals(transaction.status, "voided")

    @patch("braintree.Transaction.hold_in_escrow")
    def test_hold_in_escrow(self, transaction_hold_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            amount=decimal.Decimal("10.00"),
        )
        transaction_hold_mock.return_value = get_fake_success_transaction(
            escrow_status='held'
        )
        transaction.hold_in_escrow()
        self.assertEquals(transaction.escrow_status, "held")

    @patch("braintree.Transaction.release_from_escrow")
    def test_release_from_escrow(self, transaction_release_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            amount=decimal.Decimal("10.00"),
        )
        transaction_release_mock.return_value = get_fake_success_transaction(
            escrow_status='release_pending'
        )
        transaction.release_from_escrow()
        self.assertEquals(transaction.escrow_status, "release_pending")

    @patch("braintree.Transaction.cancel_release")
    def test_cancel_release(self, transaction_cancel_release_mock):
        transaction = Transaction.objects.create(
            braintree_id="tx_XXXXXX",
            amount=decimal.Decimal("10.00"),
        )
        transaction_cancel_release_mock.return_value = get_fake_success_transaction(
            escrow_status='held'
        )
        transaction.cancel_release()
        self.assertEquals(transaction.escrow_status, "held")
