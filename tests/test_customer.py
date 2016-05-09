"""
.. module:: dj-braintree.tests.test_customer
   :synopsis: dj-braintree Customer Model Tests.

.. moduleauthor:: Daniel Greenfeld (@pydanny)
.. moduleauthor:: Alex Kavanaugh (@kavdev)
.. moduleauthor:: Michael Thornhill (@mthornhill)

"""

import datetime
import decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from mock import patch, PropertyMock, MagicMock
from unittest2 import TestCase as AssertWarnsEnabledTestCase

from djbraintree.models import Customer, Transaction


class TestCustomer(TestCase):
    # fake_current_subscription = CurrentSubscription(plan="test_plan",
    #                                                 quantity=1,
    #                                                 start=timezone.now(),
    #                                                 amount=decimal.Decimal(25.00))
    #
    # fake_current_subscription_cancelled_in_stripe = CurrentSubscription(plan="test_plan",
    #                                                                     quantity=1,
    #                                                                     start=timezone.now(),
    #                                                                     amount=decimal.Decimal(25.00),
    #                                                                     status=CurrentSubscription.STATUS_ACTIVE)

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="patrick",
                                                         email="patrick@gmail.com")
        self.customer = Customer.objects.create(
            subscriber=self.user,
            braintree_id="cus_xxxxxxxxxxxxxxx",
        )

    def test_tostring(self):
        self.assertEquals(
            "<patrick, email=patrick@gmail.com, braintree_id=cus_xxxxxxxxxxxxxxx>",
            str(self.customer))

    @patch("braintree.Customer.find")
    def test_customer_delete(self, customer_retrieve_fake):
        braintree_id = self.customer.braintree_id
        self.customer.delete()
        customer = Customer.objects.get(braintree_id=self.customer.braintree_id)
        self.assertTrue(customer.entity is None)

    # @patch("braintree.Customer.find")
    # def test_customer_delete_same_as_purge(self, customer_retrieve_fake):
    #     self.customer.delete()
    #     customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
    #     self.assertTrue(customer.subscriber is None)
    #     self.assertTrue(customer.card_fingerprint == "")
    #     self.assertTrue(customer.card_last_4 == "")
    #     self.assertTrue(customer.card_kind == "")
    #     self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
    #
    # @patch("braintree.Customer.find")
    # def test_customer_purge_raises_customer_exception(self, customer_retrieve_mock):
    #     customer_retrieve_mock.side_effect = braintree.InvalidRequestError("No such customer:", "blah")
    #
    #     self.customer.purge()
    #     customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
    #     self.assertTrue(customer.subscriber is None)
    #     self.assertTrue(customer.card_fingerprint == "")
    #     self.assertTrue(customer.card_last_4 == "")
    #     self.assertTrue(customer.card_kind == "")
    #     self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
    #
    #     customer_retrieve_mock.assert_called_once_with(self.customer.stripe_id)
    #
    # @patch("braintree.Customer.find")
    # def test_customer_delete_raises_unexpected_exception(self, customer_retrieve_mock):
    #     customer_retrieve_mock.side_effect = braintree.InvalidRequestError("Unexpected Exception", "blah")
    #
    #     with self.assertRaisesMessage(braintree.InvalidRequestError, "Unexpected Exception"):
    #         self.customer.purge()
    #
    #     customer_retrieve_mock.assert_called_once_with(self.customer.stripe_id)

    def test_change_charge(self):
        self.assertTrue(self.customer.can_charge())

    @patch("braintree.Customer.find")
    def test_cannot_charge(self, customer_retrieve_fake):
        self.customer.delete()
        self.assertFalse(self.customer.can_charge())

    def test_transaction_accepts_only_decimals(self):
        with self.assertRaises(ValueError):
            self.customer.charge(10)

    @patch("braintree.Transaction.find")
    def test_record_transaction(self, transaction_retrieve_mock):
        transaction_retrieve_mock.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        obj = self.customer.record_transaction("ch_XXXXXX")
        self.assertEquals(Transaction.objects.get(stripe_id="ch_XXXXXX").pk,
                          obj.pk)
        self.assertEquals(obj.paid, True)
        self.assertEquals(obj.disputed, False)
        self.assertEquals(obj.refunded, False)
        self.assertEquals(obj.amount_refunded, None)

    @patch("braintree.Transaction.find")
    def test_refund_transaction(self, transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("10.00"),
            paid=True,
            refunded=False,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": True,
            "captured": True,
            "amount_refunded": 1000,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction.refund()
        transaction2 = Transaction.objects.get(stripe_id="ch_XXXXXX")
        self.assertEquals(transaction2.refunded, True)
        self.assertEquals(transaction2.amount_refunded,
                          decimal.Decimal("10.00"))

    @patch("braintree.Transaction.find")
    def test_refund_transaction_passes_extra_args(self,
                                                  transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("10.00"),
            paid=True,
            refunded=False,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": True,
            "captured": True,
            "amount_refunded": 1000,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction.refund(
            amount=decimal.Decimal("10.00"),
            reverse_transfer=True,
            refund_application_fee=False
        )
        _, kwargs = transaction_retrieve_mock.return_value.refund.call_args
        self.assertEquals(kwargs["reverse_transfer"], True)
        self.assertEquals(kwargs["refund_application_fee"], False)

    @patch("braintree.Transaction.find")
    def test_capture_transaction(self, transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("10.00"),
            paid=True,
            refunded=False,
            captured=False,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        transaction_retrieve_mock.return_value.capture.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": True,
            "captured": True,
            "amount_refunded": 1000,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction2 = transaction.capture()
        self.assertEquals(transaction2.captured, True)

    @patch("braintree.Transaction.find")
    def test_refund_transaction_object_returned(self,
                                                transaction_retrieve_mock):
        transaction = Transaction.objects.create(
            stripe_id="ch_XXXXXX",
            customer=self.customer,
            card_last_4="4323",
            card_kind="Visa",
            amount=decimal.Decimal("10.00"),
            paid=True,
            refunded=False,
            fee=decimal.Decimal("4.99"),
            disputed=False
        )
        transaction_retrieve_mock.return_value.refund.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": True,
            "captured": True,
            "amount_refunded": 1000,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        transaction2 = transaction.refund()
        self.assertEquals(transaction2.refunded, True)
        self.assertEquals(transaction2.amount_refunded,
                          decimal.Decimal("10.00"))

    def test_calculate_refund_amount_full_refund(self):
        transaction = Transaction(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_refund_amount(),
            50000
        )

    def test_calculate_refund_amount_partial_refund(self):
        transaction = Transaction(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_refund_amount(
                amount=decimal.Decimal("300.00")),
            30000
        )

    def test_calculate_refund_above_max_refund(self):
        transaction = Transaction(
            stripe_id="ch_111111",
            customer=self.customer,
            amount=decimal.Decimal("500.00")
        )
        self.assertEquals(
            transaction.calculate_refund_amount(
                amount=decimal.Decimal("600.00")),
            50000
        )

    @patch("braintree.Transaction.find")
    @patch("braintree.Transaction.create")
    def test_transaction_converts_dollars_into_cents(self,
                                                     transaction_create_mock,
                                                     transaction_retrieve_mock):
        transaction_create_mock.return_value.id = "ch_XXXXX"
        transaction_retrieve_mock.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        self.customer.transaction(
            amount=decimal.Decimal("10.00")
        )
        _, kwargs = transaction_create_mock.call_args
        self.assertEquals(kwargs["amount"], 1000)

    # @patch("braintree.Transaction.find")
    # @patch("braintree.Transaction.create")
    # def test_transaction_doesnt_require_invoice(self, transaction_create_mock,
    #                                             transaction_retrieve_mock):
    #     transaction_retrieve_mock.return_value = transaction_create_mock.return_value = {
    #         "id": "ch_XXXXXX",
    #         "card": {
    #             "last4": "4323",
    #             "type": "Visa"
    #         },
    #         "amount": 1000,
    #         "paid": True,
    #         "refunded": False,
    #         "captured": True,
    #         "fee": 499,
    #         "dispute": None,
    #         "created": 1363911708,
    #         "customer": "cus_xxxxxxxxxxxxxxx",
    #         "invoice": "in_30Kg7Arb0132UK",
    #     }
    #
    #     try:
    #         self.customer.transaction(
    #             amount=decimal.Decimal("10.00")
    #         )
    #     except Invoice.DoesNotExist:
    #         self.fail(msg="Braintree Transaction shouldn't require an Invoice")

    @patch("braintree.Transaction.find")
    @patch("braintree.Transaction.create")
    def test_transaction_passes_extra_arguments(self, transaction_create_mock,
                                                transaction_retrieve_mock):
        transaction_create_mock.return_value.id = "ch_XXXXX"
        transaction_retrieve_mock.return_value = {
            "id": "ch_XXXXXX",
            "card": {
                "last4": "4323",
                "type": "Visa"
            },
            "amount": 1000,
            "paid": True,
            "refunded": False,
            "captured": True,
            "fee": 499,
            "dispute": None,
            "created": 1363911708,
            "customer": "cus_xxxxxxxxxxxxxxx"
        }
        self.customer.transaction(
            amount=decimal.Decimal("10.00"),
            capture=True,
            destination='a_stripe_client_id'
        )
        _, kwargs = transaction_create_mock.call_args
        self.assertEquals(kwargs["capture"], True)
        self.assertEquals(kwargs["destination"], 'a_stripe_client_id')

    @patch(
        "djbraintree.models.djbraintree_settings.trial_period_for_subscriber_callback",
        return_value="donkey")
    @patch("braintree.Customer.create",
           return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_create_trial_callback(self, customer_create_mock, callback_mock):
        user = get_user_model().objects.create_user(username="test",
                                                    email="test@gmail.com")
        Customer.create(user)

        customer_create_mock.assert_called_once_with(email=user.email)
        callback_mock.assert_called_once_with(user)

    @patch("djbraintree.models.Customer.subscribe")
    @patch("djbraintree.models.djbraintree_settings.DEFAULT_PLAN",
           new_callable=PropertyMock, return_value="schreck")
    @patch(
        "djbraintree.models.djbraintree_settings.trial_period_for_subscriber_callback",
        return_value="donkey")
    @patch("braintree.Customer.create",
           return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_create_default_plan(self, customer_create_mock, callback_mock,
                                 default_plan_fake, subscribe_mock):
        user = get_user_model().objects.create_user(username="test",
                                                    email="test@gmail.com")
        Customer.create(user)

        customer_create_mock.assert_called_once_with(email=user.email)
        callback_mock.assert_called_once_with(user)
        subscribe_mock.assert_called_once_with(plan=default_plan_fake,
                                               trial_days="donkey")

    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock)
    def test_update_card(self, customer_stripe_customer_mock):
        customer_stripe_customer_mock.return_value = PropertyMock(
            active_card=PropertyMock(
                fingerprint="test_fingerprint",
                last4="1234",
                type="test_type",
                exp_month=12,
                exp_year=2020
            )
        )

        self.customer.update_card("test")

        self.assertEqual("test_fingerprint", self.customer.card_fingerprint)
        self.assertEqual("1234", self.customer.card_last_4)
        self.assertEqual("test_type", self.customer.card_kind)
        self.assertEqual(12, self.customer.card_exp_month)
        self.assertEqual(2020, self.customer.card_exp_year)

    @patch("djbraintree.models.Customer.invoices", new_callable=PropertyMock,
           return_value=PropertyMock(name="filter", filter=MagicMock(
               return_value=[MagicMock(name="inv", retry=MagicMock(name="retry",
                                                                   return_value="test"))])))
    @patch("djbraintree.models.Customer.sync_invoices")
    def test_retry_unpaid_invoices(self, sync_invoices_mock, invoices_mock):
        self.customer.retry_unpaid_invoices()

        sync_invoices_mock.assert_called_once_with()
        # TODO: Figure out how to assert on filter and retry mocks
    #
    # @patch("djbraintree.models.Customer.invoices", new_callable=PropertyMock,
    #        return_value=PropertyMock(name="filter", filter=MagicMock(
    #            return_value=[MagicMock(name="inv", retry=MagicMock(name="retry",
    #                                                                return_value="test",
    #                                                                side_effect=braintree.InvalidRequestError(
    #                                                                    "Invoice is already paid",
    #                                                                    "blah")))])))
    @patch("djbraintree.models.Customer.sync_invoices")
    def test_retry_unpaid_invoices_expected_exception(self, sync_invoices_mock,
                                                      invoices_mock):
        try:
            self.customer.retry_unpaid_invoices()
        except:
            self.fail("Exception was unexpectedly raise.")
    #
    # @patch("djbraintree.models.Customer.invoices", new_callable=PropertyMock,
    #        return_value=PropertyMock(name="filter", filter=MagicMock(
    #            return_value=[MagicMock(name="inv", retry=MagicMock(name="retry",
    #                                                                return_value="test",
    #                                                                side_effect=braintree.InvalidRequestError(
    #                                                                    "This should fail!",
    #                                                                    "blah")))])))
    # @patch("djbraintree.models.Customer.sync_invoices")
    # def test_retry_unpaid_invoices_unexpected_exception(self,
    #                                                     sync_invoices_mock,
    #                                                     invoices_mock):
    #     with self.assertRaisesMessage(braintree.InvalidRequestError,
    #                                   "This should fail!"):
    #         self.customer.retry_unpaid_invoices()

    @patch("braintree.Invoice.create")
    def test_send_invoice_success(self, invoice_create_mock):
        return_status = self.customer.send_invoice()
        self.assertTrue(return_status)

        invoice_create_mock.assert_called_once_with(
            customer=self.customer.stripe_id)

    # @patch("braintree.Invoice.create")
    # def test_send_invoice_failure(self, invoice_create_mock):
    #     invoice_create_mock.side_effect = braintree.InvalidRequestError(
    #         "Invoice creation failed.", "blah")
    #
    #     return_status = self.customer.send_invoice()
    #     self.assertFalse(return_status)
    #
    #     invoice_create_mock.assert_called_once_with(
    #         customer=self.customer.stripe_id)

    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock)
    def test_sync_active_card(self, stripe_customer_mock):
        stripe_customer_mock.return_value = PropertyMock(
            active_card=PropertyMock(
                fingerprint="cherry",
                last4="4429",
                type="apple",
                exp_month=12,
                exp_year=2020,
            ),
            deleted=False
        )

        self.customer.sync()
        self.assertEqual("cherry", self.customer.card_fingerprint)
        self.assertEqual("4429", self.customer.card_last_4)
        self.assertEqual("apple", self.customer.card_kind)
        self.assertEqual(12, self.customer.card_exp_month)
        self.assertEqual(2020, self.customer.card_exp_year)

    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(active_card=None, deleted=False))
    def test_sync_no_card(self, stripe_customer_mock):
        self.customer.sync()
        self.assertEqual("YYYYYYYY", self.customer.card_fingerprint)
        self.assertEqual("2342", self.customer.card_last_4)
        self.assertEqual("Visa", self.customer.card_kind)

    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(deleted=True))
    def test_sync_deleted_in_stripe(self, stripe_customer_mock):
        self.customer.sync()
        customer = Customer.objects.get(stripe_id=self.customer.stripe_id)
        self.assertTrue(customer.subscriber is None)
        self.assertTrue(customer.card_fingerprint == "")
        self.assertTrue(customer.card_last_4 == "")
        self.assertTrue(customer.card_kind == "")
        self.assertTrue(
            get_user_model().objects.filter(pk=self.user.pk).exists())

    @patch("djbraintree.models.Invoice.sync_from_stripe_data")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(invoices=MagicMock(
               return_value=PropertyMock(data=["apple", "orange", "pear"]))))
    def test_sync_invoices(self, stripe_customer_mock,
                           sync_from_stripe_data_mock):
        self.customer.sync_invoices()

        sync_from_stripe_data_mock.assert_any_call("apple", send_receipt=False)
        sync_from_stripe_data_mock.assert_any_call("orange", send_receipt=False)
        sync_from_stripe_data_mock.assert_any_call("pear", send_receipt=False)

        self.assertEqual(3, sync_from_stripe_data_mock.call_count)

    @patch("djbraintree.models.Invoice.sync_from_stripe_data")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(
               invoices=MagicMock(return_value=PropertyMock(data=[]))))
    def test_sync_invoices_none(self, stripe_customer_mock,
                                sync_from_stripe_data_mock):
        self.customer.sync_invoices()

        self.assertFalse(sync_from_stripe_data_mock.called)

    @patch("djbraintree.models.Customer.record_transaction")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(transactions=MagicMock(
               return_value=PropertyMock(data=[PropertyMock(id="herbst"),
                                               PropertyMock(id="winter"),
                                               PropertyMock(id="fruehling"),
                                               PropertyMock(id="sommer")]))))
    def test_sync_transactions(self, stripe_customer_mock,
                               record_transaction_mock):
        self.customer.sync_transactions()

        record_transaction_mock.assert_any_call("herbst")
        record_transaction_mock.assert_any_call("winter")
        record_transaction_mock.assert_any_call("fruehling")
        record_transaction_mock.assert_any_call("sommer")

        self.assertEqual(4, record_transaction_mock.call_count)

    @patch("djbraintree.models.Customer.record_transaction")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(
               transactions=MagicMock(return_value=PropertyMock(data=[]))))
    def test_sync_transactions_none(self, stripe_customer_mock,
                                    record_transaction_mock):
        self.customer.sync_transactions()

        self.assertFalse(record_transaction_mock.called)

    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock,
           return_value=PropertyMock(subscription=None))
    def test_sync_current_subscription_no_stripe_subscription(self,
                                                              stripe_customer_mock):
        self.assertEqual(None, self.customer.sync_current_subscription())

    # @patch("djbraintree.models.djbraintree_settings.plan_from_stripe_id",
    #        return_value="test_plan")
    # @patch("djbraintree.models.convert_tstamp",
    #        return_value=timezone.make_aware(datetime.datetime(2015, 6, 19)))
    # @patch("djbraintree.models.Customer.current_subscription",
    #        new_callable=PropertyMock, return_value=fake_current_subscription)
    # @patch("djbraintree.models.Customer.stripe_customer",
    #        new_callable=PropertyMock, return_value=PropertyMock(
    #         subscription=PropertyMock(plan=PropertyMock(id="fish", amount=5000),
    #                                   quantity=5,
    #                                   trial_start=False,
    #                                   trial_end=False,
    #                                   cancel_at_period_end=False,
    #                                   status="tree")))
    # def test_sync_current_subscription_update_no_trial(self,
    #                                                    stripe_customer_mock,
    #                                                    customer_subscription_mock,
    #                                                    convert_tstamp_fake,
    #                                                    plan_getter_mock):
    #     tz_test_time = timezone.make_aware(datetime.datetime(2015, 6, 19))
    #
    #     self.customer.sync_current_subscription()
    #
    #     plan_getter_mock.assert_called_with("fish")
    #
    #     self.assertEqual("test_plan", self.fake_current_subscription.plan)
    #     self.assertEqual(decimal.Decimal("50.00"),
    #                      self.fake_current_subscription.amount)
    #     self.assertEqual("tree", self.fake_current_subscription.status)
    #     self.assertEqual(5, self.fake_current_subscription.quantity)
    #     self.assertEqual(False,
    #                      self.fake_current_subscription.cancel_at_period_end)
    #     self.assertEqual(tz_test_time,
    #                      self.fake_current_subscription.canceled_at)
    #     self.assertEqual(tz_test_time, self.fake_current_subscription.start)
    #     self.assertEqual(tz_test_time,
    #                      self.fake_current_subscription.current_period_start)
    #     self.assertEqual(tz_test_time,
    #                      self.fake_current_subscription.current_period_end)
    #     self.assertEqual(None, self.fake_current_subscription.trial_start)
    #     self.assertEqual(None, self.fake_current_subscription.trial_end)

    # @patch("djbraintree.models.Customer.current_subscription",
    #        new_callable=PropertyMock,
    #        return_value=fake_current_subscription_cancelled_in_stripe)
    # @patch("djbraintree.models.Customer.stripe_customer",
    #        new_callable=PropertyMock,
    #        return_value=PropertyMock(subscription=None))
    # def test_sync_current_subscription_subscription_cancelled_from_Braintree(
    #     self, stripe_customer_mock, customer_subscription_mock):
    #     self.assertEqual(CurrentSubscription.STATUS_CANCELLED,
    #                      self.customer.sync_current_subscription().status)

    @patch("djbraintree.models.Customer.send_invoice")
    @patch("djbraintree.models.Customer.sync_current_subscription")
    @patch("djbraintree.models.Customer.stripe_customer.update_subscription")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock, return_value=PropertyMock())
    def test_subscribe_trial_plan(self, stripe_customer_mock,
                                  update_subscription_mock,
                                  sync_subscription_mock, send_invoice_mock):
        trial_days = 7  # From settings

        self.customer.subscribe(plan="test_trial")
        sync_subscription_mock.assert_called_once_with()
        send_invoice_mock.assert_called_once_with()

        _, call_kwargs = update_subscription_mock.call_args

        self.assertIn("trial_end", call_kwargs)
        self.assertLessEqual(call_kwargs["trial_end"],
                             timezone.now() + datetime.timedelta(
                                 days=trial_days))

    @patch("djbraintree.models.Customer.send_invoice")
    @patch("djbraintree.models.Customer.sync_current_subscription")
    @patch("djbraintree.models.Customer.stripe_customer.update_subscription")
    @patch("djbraintree.models.Customer.stripe_customer",
           new_callable=PropertyMock, return_value=PropertyMock())
    def test_subscribe_trial_days_kwarg(self, stripe_customer_mock,
                                        update_subscription_mock,
                                        sync_subscription_mock,
                                        send_invoice_mock):
        trial_days = 9

        self.customer.subscribe(plan="test", trial_days=trial_days)
        sync_subscription_mock.assert_called_once_with()
        send_invoice_mock.assert_called_once_with()

        _, call_kwargs = update_subscription_mock.call_args

        self.assertIn("trial_end", call_kwargs)
        self.assertLessEqual(call_kwargs["trial_end"],
                             timezone.now() + datetime.timedelta(
                                 days=trial_days))

    # @patch("djbraintree.models.Customer.send_invoice")
    # @patch("djbraintree.models.Customer.sync_current_subscription")
    # @patch("djbraintree.models.Customer.current_subscription",
    #        new_callable=PropertyMock, return_value=fake_current_subscription)
    # @patch("djbraintree.models.Customer.stripe_customer",
    #        new_callable=PropertyMock, return_value=PropertyMock())
    # def test_subscribe_not_charge_immediately(self, stripe_customer_mock,
    #                                           customer_subscription_mock,
    #                                           sync_subscription_mock,
    #                                           send_invoice_mock):
    #     self.customer.subscribe(plan="test", charge_immediately=False)
    #     sync_subscription_mock.assert_called_once_with()
    #     self.assertFalse(send_invoice_mock.called)

    @patch("djbraintree.models.Transaction.send_receipt")
    @patch("djbraintree.models.Customer.record_transaction",
           return_value=Transaction())
    @patch("braintree.Transaction.create",
           return_value={"id": "test_transaction_id"})
    def test_transaction_not_send_receipt(self, transaction_create_mock,
                                          record_transaction_mock,
                                          send_receipt_mock):

        self.customer.charge(amount=decimal.Decimal("50.00"),
                             send_receipt=False)
        self.assertTrue(transaction_create_mock.called)
        record_transaction_mock.assert_called_once_with("test_transaction_id")
        self.assertFalse(send_receipt_mock.called)

    @patch("braintree.InvoiceItem.create")
    def test_add_invoice_item(self, invoice_item_create_mock):
        self.customer.add_invoice_item(amount=decimal.Decimal("50.00"),
                                       currency="eur", invoice_id=77,
                                       description="test")

        invoice_item_create_mock.assert_called_once_with(amount=5000,
                                                         currency="eur",
                                                         invoice=77,
                                                         description="test",
                                                         customer=self.customer.stripe_id)

    def test_add_invoice_item_bad_decimal(self):
        with self.assertRaisesMessage(ValueError,
                                      "You must supply a decimal value representing dollars."):
            self.customer.add_invoice_item(amount=5000)

