"""
.. module:: dj-braintree.tests.test_integrations.test_sync
   :synopsis: dj-braintree Sync Method Tests.

.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""

import sys

from django.conf import settings
from django.test.testcases import TestCase
from django.contrib.auth import get_user_model

from djbraintree.braintree_objects import configure_braintree
from djbraintree.models import Transaction
from djbraintree.sync import sync_entity
from unittest.case import skip

# These tests will be converted to sync tests on the customer model

if False:
    @skip
    class TestSyncSubscriber(TestCase):

        def setUp(self):
            self.user = get_user_model().objects.create_user(username="testsync", email="testsync@test.com")

        def test_new_customer(self):
            customer = sync_entity(self.user)
            transactions = Transaction.objects.filter(customer=customer)

            # There shouldn't be any items attached to the customer
            self.assertEqual(0, len(transactions), "Transactions are unexpectedly associated with a new customer object.")

        def test_existing_customer(self):
            customerA = sync_entity(self.user)
            customerB = sync_entity(self.user)

            self.assertEqual(customerA, customerB, "Customers returned are not equal.")

        def test_bad_sync(self):
            customer = sync_entity(self.user)
            customer.braintree_id = "fake_customer_id"
            customer.save()

            sync_entity(self.user)

            self.assertEqual("ERROR: No such customer: fake_customer_id", sys.stdout.getvalue().strip())

        def test_transaction_sync(self):
            # Initialize braintree
            import braintree
            configure_braintree()

            customer = sync_entity(self.user)
            transactions = Transaction.objects.filter(customer=customer)

            # There shouldn't be any items attached to the customer
            self.assertEqual(0, len(transactions), "Transactions are unexpectedly associated with a new customer object.")

            token = braintree.Token.create(
                card={
                    "number": '4242424242424242',
                    "exp_month": 12,
                    "exp_year": 2016,
                    "cvc": '123'
                },
            )

            customer.update_card(token.id)

            braintree.Transaction.create(
                amount=int(10 * 100),  # Convert dollars into cents
                currency="USD",
                customer=customer.braintree_id,
                description="Test Transaction in test_transaction_sync",
            )

            customer = sync_entity(self.user)
            transactions = Transaction.objects.filter(customer=customer)
            self.assertEqual(1, len(transactions), "Unexpected number of transactions associated with a new customer object.")
