"""
.. module:: dj-braintree.tests.test_customer
   :synopsis: dj-braintree Customer Model Tests.

.. moduleauthor:: Daniel Greenfeld (@pydanny)
.. moduleauthor:: Alex Kavanaugh (@kavdev)
.. moduleauthor:: Michael Thornhill (@mthornhill)

"""

import decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from mock import patch, PropertyMock, MagicMock

from djbraintree.models import Customer, Transaction
from tests import get_fake_success_transaction, get_fake_customer


class TestCustomer(TestCase):
    # fake_current_subscription = CurrentSubscription(plan="test_plan",
    #                                                 quantity=1,
    #                                                 start=timezone.now(),
    #                                                 amount=decimal.Decimal(25.00))
    #
    # fake_current_subscription_cancelled_in_braintree = CurrentSubscription(plan="test_plan",
    #                                                                     quantity=1,
    #                                                                     start=timezone.now(),
    #                                                                     amount=decimal.Decimal(25.00),
    #                                                                     status=CurrentSubscription.STATUS_ACTIVE)

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="patrick",
                                                         email="patrick@gmail.com")
        self.customer = Customer.objects.create(
            entity=self.user,
            braintree_id="cus_xxxxxxxxxxxxxxx",
        )

    def test_tostring(self):
        self.assertEquals(
            "<patrick, email=patrick@gmail.com, braintree_id=cus_xxxxxxxxxxxxxxx>",
            str(self.customer))

    def test_sync_from_braintree_object(self):
        result = get_fake_customer()
        customer = Customer.sync_from_braintree_object(result.customer)

        self.assertEqual(u'customer_123', customer.braintree_id)

    @patch("braintree.Customer.create", return_value=get_fake_customer(id='cus_xxx1234567890'))
    def test_create(self, create_mock):
        user = get_user_model().objects.create_user(username="tobias",
                                                         email="tobias@mail.com")
        customer = Customer.create(entity=user)
        self.assertEqual(customer.braintree_id, 'cus_xxx1234567890')

    @patch("braintree.Customer.create",return_value=get_fake_customer(id='cus_xxx1234567890'))
    def test_get_or_create(self, create_mock):
        customer, created = Customer.get_or_create(self.user)
        self.assertFalse(created)
        self.assertEqual(customer.entity, self.user)

    @patch("braintree.Customer.create",
           return_value=get_fake_customer(id='cus_xxx1234567890'))
    def test_get_or_create(self, create_mock):

        user = get_user_model().objects.create_user(username="tobias",
                                                         email="tobias@mail.com")
        customer, created = Customer.get_or_create(entity=user)
        self.assertTrue(created)
        self.assertEqual(customer.entity, user)

    # @patch("braintree.Customer.delete")
    # def test_customer_delete(self, customer_delete_fake):
    #     braintree_id = self.customer.braintree_id
    #     self.customer.delete()
    #     customer_delete_fake.assert_called_once_with(braintree_id)

    # @patch("braintree.Customer.find")
    # def test_customer_delete_same_as_purge(self, customer_retrieve_fake):
    #     self.customer.delete()
    #     customer = Customer.objects.get(braintree_id=self.customer.braintree_id)
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
    #     customer = Customer.objects.get(braintree_id=self.customer.braintree_id)
    #     self.assertTrue(customer.subscriber is None)
    #     self.assertTrue(customer.card_fingerprint == "")
    #     self.assertTrue(customer.card_last_4 == "")
    #     self.assertTrue(customer.card_kind == "")
    #     self.assertTrue(get_user_model().objects.filter(pk=self.user.pk).exists())
    #
    #     customer_retrieve_mock.assert_called_once_with(self.customer.braintree_id)
    #
    # @patch("braintree.Customer.find")
    # def test_customer_delete_raises_unexpected_exception(self, customer_retrieve_mock):
    #     customer_retrieve_mock.side_effect = braintree.InvalidRequestError("Unexpected Exception", "blah")
    #
    #     with self.assertRaisesMessage(braintree.InvalidRequestError, "Unexpected Exception"):
    #         self.customer.purge()
    #
    #     customer_retrieve_mock.assert_called_once_with(self.customer.braintree_id)

    # def test_change_charge(self):
    #     self.assertTrue(self.customer.can_charge())

    # @patch("braintree.Customer.find")
    # def test_cannot_charge(self, customer_retrieve_fake):
    #     self.customer.delete()
    #     self.assertFalse(self.customer.can_charge())

    # def test_charge_accepts_only_decimals(self):
    #     with self.assertRaises(ValueError):
    #         self.customer.charge(10)
    #
    # def test_charge_requires_payment_method(self):
    #     e = None
    #     try:
    #         self.customer.charge(decimal.Decimal('10.00'))
    #     except ValueError as error:
    #         e = error
    #     self.assertEquals(e.message,
    #                       "You must supply a payment method nonce or token.")
    #
    # @patch("braintree.Transaction.find")
    # @patch("braintree.Transaction.sale")
    # def test_charge_passes_extra_arguments(self,
    #                                        transaction_create_mock,
    #                                        transaction_retrieve_mock):
    #     transaction_create_mock.return_value.id = "ch_XXXXX"
    #     transaction_retrieve_mock.return_value = {
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
    #         "customer": "cus_xxxxxxxxxxxxxxx"
    #     }
    #     self.customer.charge(
    #         amount=decimal.Decimal("10.00"),
    #         payment_method_token="zxc1234",
    #         options={'submit_for_settlement': True},
    #         merchant_account="submerchant_xxxxxxx"
    #     )
    #     kwargs = transaction_create_mock.call_args[0][0]
    #     self.assertEquals(kwargs["merchant_account"], "submerchant_xxxxxxx")
    #     self.assertEquals(kwargs["customer_id"], self.customer.braintree_id)
    #
    # @patch("braintree.Transaction.find")
    # def test_record_transaction(self, transaction_retrieve_mock):
    #     transaction_retrieve_mock.return_value = {
    #         "id": "tx_XXXXXX",
    #
    #     }
    #     result = get_fake_success_transaction()
    #     tx_obj = result.transaction
    #     tx_obj.id = "tx_XXXXXX"
    #     obj = self.customer.record_transaction(tx_obj)
    #     self.assertEquals(Transaction.objects.get(braintree_id="tx_XXXXXX").pk,
    #                       obj.pk)
    #     self.assertEquals(obj.amount, decimal.Decimal('9.95'))

    #
    # @patch(
    #     "djbraintree.models.djbraintree_settings.trial_period_for_subscriber_callback",
    #     return_value="donkey")
    # @patch("braintree.Customer.create",
    #        return_value=PropertyMock(id="cus_xxx1234567890"))
    # def test_create_trial_callback(self, customer_create_mock, callback_mock):
    #     user = get_user_model().objects.create_user(username="test",
    #                                                 email="test@gmail.com")
    #     Customer.create(user)
    #
    #     customer_create_mock.assert_called_once_with(email=user.email)
    #     callback_mock.assert_called_once_with(user)
    #
    # @patch("djbraintree.models.Customer.subscribe")
    # @patch("djbraintree.models.djbraintree_settings.DEFAULT_PLAN",
    #        new_callable=PropertyMock, return_value="schreck")
    # @patch(
    #     "djbraintree.models.djbraintree_settings.trial_period_for_subscriber_callback",
    #     return_value="donkey")
    # @patch("braintree.Customer.create",
    #        return_value=PropertyMock(id="cus_xxx1234567890"))
    # def test_create_default_plan(self, customer_create_mock, callback_mock,
    #                              default_plan_fake, subscribe_mock):
    #     user = get_user_model().objects.create_user(username="test",
    #                                                 email="test@gmail.com")
    #     Customer.create(user)
    #
    #     customer_create_mock.assert_called_once_with(email=user.email)
    #     callback_mock.assert_called_once_with(user)
    #     subscribe_mock.assert_called_once_with(plan=default_plan_fake,
    #                                            trial_days="donkey")

    # @patch("djbraintree.models.Customer.braintree_customer",
    #        new_callable=PropertyMock)
    # def test_update_card(self, customer_braintree_customer_mock):
    #     customer_braintree_customer_mock.return_value = PropertyMock(
    #         active_card=PropertyMock(
    #             fingerprint="test_fingerprint",
    #             last4="1234",
    #             type="test_type",
    #             exp_month=12,
    #             exp_year=2020
    #         )
    #     )
    #
    #     self.customer.update_card("test")
    #
    #     self.assertEqual("test_fingerprint", self.customer.card_fingerprint)
    #     self.assertEqual("1234", self.customer.card_last_4)
    #     self.assertEqual("test_type", self.customer.card_kind)
    #     self.assertEqual(12, self.customer.card_exp_month)
    #     self.assertEqual(2020, self.customer.card_exp_year)

    # @patch("djbraintree.models.Customer.braintree_customer",
    #        new_callable=PropertyMock)
    # def test_sync_active_card(self, braintree_customer_mock):
    #     braintree_customer_mock.return_value = PropertyMock(
    #         active_card=PropertyMock(
    #             fingerprint="cherry",
    #             last4="4429",
    #             type="apple",
    #             exp_month=12,
    #             exp_year=2020,
    #         ),
    #         deleted=False
    #     )
    #
    #     self.customer.sync()
    #     self.assertEqual("cherry", self.customer.card_fingerprint)
    #     self.assertEqual("4429", self.customer.card_last_4)
    #     self.assertEqual("apple", self.customer.card_kind)
    #     self.assertEqual(12, self.customer.card_exp_month)
    #     self.assertEqual(2020, self.customer.card_exp_year)
    #
    # @patch("djbraintree.models.Customer.braintree_customer",
    #        new_callable=PropertyMock,
    #        return_value=PropertyMock(active_card=None, deleted=False))
    # def test_sync_no_card(self, braintree_customer_mock):
    #     self.customer.sync()
    #     self.assertEqual("YYYYYYYY", self.customer.card_fingerprint)
    #     self.assertEqual("2342", self.customer.card_last_4)
    #     self.assertEqual("Visa", self.customer.card_kind)
    #
    #
    # @patch("braintree.Customer.find",
    #        new_callable=PropertyMock,
    #        return_value=PropertyMock(deleted=True))
    # def test_sync_deleted_in_braintree(self, braintree_customer_mock):
    #     self.customer.sync()
    #     customer = Customer.objects.get(braintree_id=self.customer.braintree_id)
    #     self.assertTrue(customer.entity is None)
    #     self.assertTrue(
    #         get_user_model().objects.filter(pk=self.user.pk).exists())
    #
    # @patch("djbraintree.models.Customer.record_transaction")
    # @patch("braintree.Customer.find",
    #        new_callable=PropertyMock,
    #        return_value=PropertyMock(transactions=MagicMock(
    #            return_value=PropertyMock(data=[PropertyMock(id="herbst"),
    #                                            PropertyMock(id="winter"),
    #                                            PropertyMock(id="fruehling"),
    #                                            PropertyMock(id="sommer")]))))
    # def test_sync_transactions(self, braintree_customer_mock,
    #                            record_transaction_mock):
    #     self.customer.sync_transactions()
    #
    #     record_transaction_mock.assert_any_call("herbst")
    #     record_transaction_mock.assert_any_call("winter")
    #     record_transaction_mock.assert_any_call("fruehling")
    #     record_transaction_mock.assert_any_call("sommer")
    #
    #     self.assertEqual(4, record_transaction_mock.call_count)
    #
    # @patch("djbraintree.models.Customer.record_transaction")
    # @patch("djbraintree.models.Customer.retrieve_transactions",
    #        return_value=PropertyMock(items=[])
    #        )
    # def test_sync_transactions_none(self, braintree_collection_mock,
    #                                 record_transaction_mock):
    #     class BraintreeCollection(object):
    #         def __init__(self):
    #             self.items = []
    #
    #     self.customer.sync_transactions(
    #         braintree_collection=BraintreeCollection())
    #
    #     self.assertFalse(record_transaction_mock.called)

        # @patch("djbraintree.models.Customer.braintree_customer",
        #        new_callable=PropertyMock,
        #        return_value=PropertyMock(subscription=None))
        # def test_sync_current_subscription_no_braintree_subscription(self,
        #                                                           braintree_customer_mock):
        #     self.assertEqual(None, self.customer.sync_current_subscription())
        #
        # @patch("djbraintree.models.djbraintree_settings.plan_from_braintree_id",
        #        return_value="test_plan")
        # @patch("djbraintree.models.convert_tstamp",
        #        return_value=timezone.make_aware(datetime.datetime(2015, 6, 19)))
        # @patch("djbraintree.models.Customer.current_subscription",
        #        new_callable=PropertyMock, return_value=fake_current_subscription)
        # @patch("djbraintree.models.Customer.braintree_customer",
        #        new_callable=PropertyMock, return_value=PropertyMock(
        #         subscription=PropertyMock(plan=PropertyMock(id="fish", amount=5000),
        #                                   quantity=5,
        #                                   trial_start=False,
        #                                   trial_end=False,
        #                                   cancel_at_period_end=False,
        #                                   status="tree")))
        # def test_sync_current_subscription_update_no_trial(self,
        #                                                    braintree_customer_mock,
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
        #        return_value=fake_current_subscription_cancelled_in_braintree)
        # @patch("djbraintree.models.Customer.braintree_customer",
        #        new_callable=PropertyMock,
        #        return_value=PropertyMock(subscription=None))
        # def test_sync_current_subscription_subscription_cancelled_from_Braintree(
        #     self, braintree_customer_mock, customer_subscription_mock):
        #     self.assertEqual(CurrentSubscription.STATUS_CANCELLED,
        #                      self.customer.sync_current_subscription().status)
        #
        # @patch("djbraintree.models.Customer.send_invoice")
        # @patch("djbraintree.models.Customer.sync_current_subscription")
        # @patch("djbraintree.models.Customer.braintree_customer.update_subscription")
        # @patch("djbraintree.models.Customer.braintree_customer",
        #        new_callable=PropertyMock, return_value=PropertyMock())
        # def test_subscribe_trial_plan(self, braintree_customer_mock,
        #                               update_subscription_mock,
        #                               sync_subscription_mock, send_invoice_mock):
        #     trial_days = 7  # From settings
        #
        #     self.customer.subscribe(plan="test_trial")
        #     sync_subscription_mock.assert_called_once_with()
        #     send_invoice_mock.assert_called_once_with()
        #
        #     _, call_kwargs = update_subscription_mock.call_args
        #
        #     self.assertIn("trial_end", call_kwargs)
        #     self.assertLessEqual(call_kwargs["trial_end"],
        #                          timezone.now() + datetime.timedelta(
        #                              days=trial_days))
        #
        # @patch("djbraintree.models.Customer.send_invoice")
        # @patch("djbraintree.models.Customer.sync_current_subscription")
        # @patch("djbraintree.models.Customer.braintree_customer.update_subscription")
        # @patch("djbraintree.models.Customer.braintree_customer",
        #        new_callable=PropertyMock, return_value=PropertyMock())
        # def test_subscribe_trial_days_kwarg(self, braintree_customer_mock,
        #                                     update_subscription_mock,
        #                                     sync_subscription_mock,
        #                                     send_invoice_mock):
        #     trial_days = 9
        #
        #     self.customer.subscribe(plan="test", trial_days=trial_days)
        #     sync_subscription_mock.assert_called_once_with()
        #     send_invoice_mock.assert_called_once_with()
        #
        #     _, call_kwargs = update_subscription_mock.call_args
        #
        #     self.assertIn("trial_end", call_kwargs)
        #     self.assertLessEqual(call_kwargs["trial_end"],
        #                          timezone.now() + datetime.timedelta(
        #                              days=trial_days))
