"""
.. module:: dj-braintree.tests.test_sync
   :synopsis: dj-braintree Sync Method Tests.

.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""

import sys

from django.test.testcases import TestCase
from django.contrib.auth import get_user_model
from mock import patch, PropertyMock

from braintree.exceptions.not_found_error import NotFoundError
from djbraintree.sync import sync_entity


class TestSyncSubscriber(TestCase):
    fake_braintree_customer = "test_braintree_customer"

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")

    @patch("djbraintree.models.Customer.sync_transactions")
    @patch("djbraintree.models.Customer.sync")
    @patch("djbraintree.models.Customer.braintree_customer", new_callable=PropertyMock, return_value=fake_braintree_customer)
    @patch("braintree.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_sync_success(self,
                          braintree_customer_create_mock,
                          braintree_customer_mock,
                          sync_mock,
                          sync_charges_mock):
        sync_entity(self.user)
        sync_mock.assert_called_once_with(cu=self.fake_braintree_customer)
        sync_charges_mock.assert_called_once_with(cu=self.fake_braintree_customer)

    @patch("djbraintree.models.Customer.sync")
    @patch("djbraintree.models.Customer.braintree_customer", new_callable=PropertyMock, return_value="test_braintree_customer")
    @patch("braintree.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_sync_fail(self, braintree_customer_create_mock, braintree_customer_mock, sync_mock):

        sync_mock.side_effect = NotFoundError("No such customer:", "blah")
        sync_entity(self.user)

        self.assertEqual("ERROR: No such customer:", sys.stdout.getvalue().strip())

#
# class TestSyncPlans(TestCase):
#
#     @patch("braintree.Plan.create")
#     def test_plan_created(self, plan_create_mock):
#         sync_plans(api_key)
#         self.assertTrue("Plan created for test", sys.stdout.getvalue().strip())
#
#         plan_create_mock.assert_any_call(amount=1000,
#                                         interval="month",
#                                         name="Test Plan 0",
#                                         currency="usd",
#                                         id="test_id_0",
#                                         interval_count=None,
#                                         trial_period_days=None,
#                                         statement_descriptor=None,
#                                         metadata=None)
#
#         plan_create_mock.assert_any_call(amount=2500,
#                                         interval="month",
#                                         name="Test Plan 1",
#                                         currency="usd",
#                                         id="test_id",
#                                         interval_count=None,
#                                         trial_period_days=None,
#                                         statement_descriptor=None,
#                                         metadata=None)
#
#         plan_create_mock.assert_any_call(amount=5000,
#                                         interval="month",
#                                         name="Test Plan 2",
#                                         currency="usd",
#                                         id="test_id_2",
#                                         interval_count=None,
#                                         trial_period_days=None,
#                                         statement_descriptor=None,
#                                         metadata=None)
#
#         plan_create_mock.assert_any_call(amount=5000,
#                                         interval="month",
#                                         name="Test Plan 3",
#                                         currency="usd",
#                                         id="test_id_3",
#                                         interval_count=None,
#                                         trial_period_days=None,
#                                         statement_descriptor=None,
#                                         metadata=None)
#
#         plan_create_mock.assert_any_call(amount=7000,
#                                         interval="month",
#                                         name="Test Plan 4",
#                                         currency="usd",
#                                         id="test_id_4",
#                                         interval_count=None,
#                                         trial_period_days=7,
#                                         statement_descriptor=None,
#                                         metadata=None)
#
#         self.assertEqual(5, plan_create_mock.call_count)
#
#     @patch("braintree.Plan.create")
#     def test_plan_exists(self, plan_create_mock):
#         plan_create_mock.side_effect = braintree.BraintreeError("Plan already exists.")
#
#         sync_plans(api_key)
#         self.assertTrue("ERROR: Plan already exists.", sys.stdout.getvalue().strip())
