"""
.. module:: dj-braintree.tests.test_views
   :synopsis: dj-braintree View Tests.

.. moduleauthor:: Daniel Greenfeld (@pydanny)
.. moduleauthor:: Alex Kavanaugh (@kavdev)

"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory
from django.test.testcases import TestCase

import stripe
from mock import patch, PropertyMock

from djbraintree import settings as djbraintree_settings
from djbraintree.models import Customer, CurrentSubscription
from djbraintree.views import ChangeCardView, HistoryView


class AccountViewTest(TestCase):
    fake_stripe_customer_id = "cus_xxx1234567890"

    def setUp(self):
        self.url = reverse("djbraintree:account")
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))

    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_autocreate_customer(self, stripe_create_customer_mock):
        self.assertEqual(Customer.objects.count(), 0)

        response = self.client.get(self.url)

        # simply visiting the page should generate a new customer record.
        stripe_create_customer_mock.assert_called_once_with(email=self.user.email)

        self.assertEqual(self.fake_stripe_customer_id, response.context["customer"].stripe_id)
        self.assertEqual(self.user, response.context["customer"].subscriber)
        self.assertEqual(Customer.objects.count(), 1)

    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_plan_list_context(self, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertEqual(djbraintree_settings.PLAN_LIST, response.context["plans"])

    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_subscription_context(self, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertEqual(None, response.context["subscription"])

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test_plan_07"))
    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_subscription_context_with_plan(self, djbraintree_customer_customer_subscription_mock, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertEqual("test_plan_07", response.context["subscription"].plan)


class ChangeCardViewTest(TestCase):

    def setUp(self):
        self.url = reverse("djbraintree:change_card")
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_get(self, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

    @patch("djbraintree.models.Customer.retry_unpaid_invoices", autospec=True)
    @patch("djbraintree.models.Customer.send_invoice", autospec=True)
    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_new_card(self, stripe_customer_mock, update_card_mock, send_invoice_mock, retry_unpaid_invoices_mock):
        self.client.post(self.url, {"stripe_token": "alpha"})
        update_card_mock.assert_called_once_with(self.user.customer, "alpha")
        send_invoice_mock.assert_called_with(self.user.customer)
        retry_unpaid_invoices_mock.assert_called_once_with(self.user.customer)

    @patch("djbraintree.models.Customer.retry_unpaid_invoices", autospec=True)
    @patch("djbraintree.models.Customer.send_invoice", autospec=True)
    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_change_card(self, stripe_customer_mock, update_card_mock, send_invoice_mock, retry_unpaid_invoices_mock):
        Customer.objects.get_or_create(subscriber=self.user, card_fingerprint="4449")
        self.assertEqual(1, Customer.objects.count())

        self.client.post(self.url, {"stripe_token": "beta"})
        self.assertEqual(1, Customer.objects.count())
        update_card_mock.assert_called_once_with(self.user.customer, "beta")
        self.assertFalse(send_invoice_mock.called)
        retry_unpaid_invoices_mock.assert_called_once_with(self.user.customer)

    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_card_error(self, stripe_create_customer_mock, update_card_mock):
        update_card_mock.side_effect = stripe.StripeError("An error occurred while processing your card.")

        response = self.client.post(self.url, {"stripe_token": "pie"})
        update_card_mock.assert_called_once_with(self.user.customer, "pie")
        self.assertIn("stripe_error", response.context)
        self.assertIn("An error occurred while processing your card.", response.context["stripe_error"])

    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_no_card(self, stripe_create_customer_mock, update_card_mock):
        update_card_mock.side_effect = stripe.StripeError("Invalid source object:")

        response = self.client.post(self.url)
        update_card_mock.assert_called_once_with(self.user.customer, None)
        self.assertIn("stripe_error", response.context)
        self.assertIn("Invalid source object:", response.context["stripe_error"])

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_get_object(self, stripe_create_customer_mock):
        view_instance = ChangeCardView()
        request = RequestFactory()
        request.user = self.user

        view_instance.request = request
        object_a = view_instance.get_object()
        object_b = view_instance.get_object()

        customer_instance = Customer.objects.get(subscriber=self.user)
        self.assertEqual(customer_instance, object_a)
        self.assertEqual(object_a, object_b)

    def test_get_success_url(self):
        view_instance = ChangeCardView()
        url = view_instance.get_post_success_url()
        self.assertEqual(reverse("djbraintree:account"), url)


class HistoryViewTest(TestCase):

    def setUp(self):
        self.url = reverse("djbraintree:history")
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_get_object(self, stripe_create_customer_mock):
        view_instance = HistoryView()
        request = RequestFactory()
        request.user = self.user

        view_instance.request = request
        object_a = view_instance.get_object()

        stripe_create_customer_mock.assert_called_once_with(email=self.user.email)

        customer_instance = Customer.objects.get(subscriber=self.user)
        self.assertEqual(customer_instance, object_a)


class SyncHistoryViewTest(TestCase):

    def setUp(self):
        self.url = reverse("djbraintree:sync_history")
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))

    @patch("djbraintree.views.sync_subscriber", new_callable=PropertyMock, return_value=PropertyMock(subscriber="pie"))
    def test_post(self, sync_subscriber_mock):
        response = self.client.post(self.url)

        sync_subscriber_mock.assert_called_once_with(self.user)

        self.assertEqual("pie", response.context["customer"].subscriber)


class ConfirmFormViewTest(TestCase):
    fake_stripe_customer_id = "cus_xxx1234567890"

    def setUp(self):
        self.plan = "test0"
        self.url = reverse("djbraintree:confirm", kwargs={'plan': self.plan})
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))       

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="something-else"))
    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_get_form_valid(self, djbraintree_customer_customer_subscription_mock, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test0"))
    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_get_form_unknown(self, djbraintree_customer_customer_subscription_mock, stripe_create_customer_mock):
        response = self.client.get(reverse("djbraintree:confirm", kwargs={'plan': 'does-not-exist'}))
        self.assertRedirects(response, reverse("djbraintree:subscribe"))

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test0"))
    @patch("stripe.Customer.create", return_value=PropertyMock(id=fake_stripe_customer_id))
    def test_get_form_invalid(self, djbraintree_customer_customer_subscription_mock, stripe_create_customer_mock):
        response = self.client.get(self.url)
        self.assertRedirects(response, reverse("djbraintree:subscribe"))

    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_valid(self, stripe_customer_mock, update_card_mock, subscribe_mock):
        self.assertEqual(0, Customer.objects.count())
        response = self.client.post(self.url, {"plan": self.plan, "stripe_token": "cake"})
        self.assertEqual(1, Customer.objects.count())
        update_card_mock.assert_called_once_with(self.user.customer, "cake")
        subscribe_mock.assert_called_once_with(self.user.customer, self.plan)

        self.assertRedirects(response, reverse("djbraintree:history"))

    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    @patch("djbraintree.models.Customer.update_card", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_no_card(self, stripe_customer_mock, update_card_mock, subscribe_mock):
        update_card_mock.side_effect = stripe.StripeError("Invalid source object:")

        response = self.client.post(self.url, {"plan": self.plan})
        self.assertEqual(200, response.status_code)
        self.assertIn("form", response.context)
        self.assertIn("Invalid source object:", response.context["form"].errors["__all__"])

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_form_invalid(self, stripe_customer_mock):
        response = self.client.post(self.url)
        self.assertEqual(200, response.status_code)
        self.assertIn("plan", response.context["form"].errors)
        self.assertIn("This field is required.", response.context["form"].errors["plan"])


class ChangePlanViewTest(TestCase):

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890_01"))
    def setUp(self, stripe_customer_mock):
        self.url = reverse("djbraintree:change_plan")
        self.user1 = get_user_model().objects.create_user(username="testuser1",
                                                         email="test@example.com",
                                                         password="123")
        self.user2 = get_user_model().objects.create_user(username="testuser2",
                                                         email="test@example.com",
                                                         password="123")

        Customer.get_or_create(subscriber=self.user1)

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    def test_post_form_invalid(self, stripe_customer_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))
        response = self.client.post(self.url)
        self.assertEqual(200, response.status_code)
        self.assertIn("plan", response.context["form"].errors)
        self.assertIn("This field is required.", response.context["form"].errors["plan"])

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890_02"))
    def test_post_new_sub_no_proration(self, stripe_customer_mock):
        self.assertTrue(self.client.login(username="testuser2", password="123"))
        response = self.client.post(self.url, {"plan": "test0"})
        self.assertEqual(200, response.status_code)
        self.assertIn("form", response.context)
        self.assertIn("You must already be subscribed to a plan before you can change it.", response.context["form"].errors["__all__"])

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test", amount=Decimal(25.00)))
    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_no_proration(self, subscribe_mock, current_subscription_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))
        response = self.client.post(self.url, {"plan": "test0"})
        self.assertRedirects(response, reverse("djbraintree:history"))

        subscribe_mock.assert_called_once_with(self.user1.customer, "test0")

    @patch("djbraintree.views.PRORATION_POLICY_FOR_UPGRADES", return_value=True)
    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test", amount=Decimal(25.00)))
    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_with_proration_downgrade(self, subscribe_mock, current_subscription_mock, proration_policy_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))
        response = self.client.post(self.url, {"plan": "test0"})
        self.assertRedirects(response, reverse("djbraintree:history"))

        subscribe_mock.assert_called_once_with(self.user1.customer, "test0")

    @patch("djbraintree.views.PRORATION_POLICY_FOR_UPGRADES", return_value=True)
    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test", amount=Decimal(25.00)))
    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_with_proration_upgrade(self, subscribe_mock, current_subscription_mock, proration_policy_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))

        response = self.client.post(self.url, {"plan": "test2"})
        self.assertRedirects(response, reverse("djbraintree:history"))

        subscribe_mock.assert_called_once_with(self.user1.customer, "test2", prorate=True)

    @patch("djbraintree.views.PRORATION_POLICY_FOR_UPGRADES", return_value=True)
    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test", amount=Decimal(25.00)))
    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_with_proration_same_plan(self, subscribe_mock, current_subscription_mock, proration_policy_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))
        response = self.client.post(self.url, {"plan": "test"})
        self.assertRedirects(response, reverse("djbraintree:history"))

        subscribe_mock.assert_called_once_with(self.user1.customer, "test")

    @patch("djbraintree.models.Customer.current_subscription", new_callable=PropertyMock, return_value=CurrentSubscription(plan="test", amount=Decimal(25.00)))
    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_same_plan(self, subscribe_mock, current_subscription_mock):
        self.assertTrue(self.client.login(username="testuser1", password="123"))
        response = self.client.post(self.url, {"plan": "test"})
        self.assertRedirects(response, reverse("djbraintree:history"))

        subscribe_mock.assert_called_once_with(self.user1.customer, "test")

    @patch("djbraintree.models.Customer.subscribe", autospec=True)
    def test_change_sub_stripe_error(self, subscribe_mock):
        subscribe_mock.side_effect = stripe.StripeError("No such plan: test_id_3")

        self.assertTrue(self.client.login(username="testuser1", password="123"))

        response = self.client.post(self.url, {"plan": "test_deletion"})
        self.assertEqual(200, response.status_code)
        self.assertIn("form", response.context)
        self.assertIn("No such plan: test_id_3", response.context["form"].errors["__all__"])


class CancelSubscriptionViewTest(TestCase):
    def setUp(self):
        self.url = reverse("djbraintree:cancel_subscription")
        self.user = get_user_model().objects.create_user(username="testuser",
                                                         email="test@example.com",
                                                         password="123")
        self.assertTrue(self.client.login(username="testuser", password="123"))

    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    @patch("djbraintree.models.Customer.cancel_subscription", return_value=CurrentSubscription(status=CurrentSubscription.STATUS_ACTIVE))
    def test_cancel_proration(self, cancel_subscription_mock, stripe_create_customer_mock):
        response = self.client.post(self.url)

        cancel_subscription_mock.assert_called_once_with(at_period_end=djbraintree_settings.CANCELLATION_AT_PERIOD_END)
        self.assertRedirects(response, reverse("djbraintree:account"))
        self.assertTrue(self.user.is_authenticated())

    @patch("djbraintree.views.auth_logout", autospec=True)
    @patch("stripe.Customer.create", return_value=PropertyMock(id="cus_xxx1234567890"))
    @patch("djbraintree.models.Customer.cancel_subscription", return_value=CurrentSubscription(status=CurrentSubscription.STATUS_CANCELLED))
    def test_cancel_no_proration(self, cancel_subscription_mock, stripe_create_customer_mock, logout_mock):
        response = self.client.post(self.url)

        cancel_subscription_mock.assert_called_once_with(at_period_end=djbraintree_settings.CANCELLATION_AT_PERIOD_END)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(logout_mock.called)
