from django.db.models.base import ModelBase
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings

from djbraintree.settings import get_subscriber_model, plan_from_stripe_id


class TestSubscriberModelRetrievalMethod(TestCase):

    def test_with_user(self):
        user_model = get_subscriber_model()
        self.assertTrue(isinstance(user_model, ModelBase))

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.Organization', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=(lambda request: request.org))
    def test_with_org(self):
        org_model = get_subscriber_model()
        self.assertTrue(isinstance(org_model, ModelBase))

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.StaticEmailOrganization', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=(lambda request: request.org))
    def test_with_org_static(self):
        org_model = get_subscriber_model()
        self.assertTrue(isinstance(org_model, ModelBase))

    @override_settings(DJBRAINTREE_PAYER_MODEL='testappStaticEmailOrganization', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=(lambda request: request.org))
    def test_bad_model_name(self):
        self.assertRaisesMessage(ImproperlyConfigured, "DJBRAINTREE_PAYER_MODEL must be of the form 'app_label.model_name'.", get_subscriber_model)

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.UnknownModel', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=(lambda request: request.org))
    def test_unknown_model(self):
        self.assertRaisesMessage(ImproperlyConfigured, "DJBRAINTREE_PAYER_MODEL refers to model 'testapp.UnknownModel' that has not been installed.", get_subscriber_model)

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.NoEmailOrganization', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=(lambda request: request.org))
    def test_no_email_model(self):
        self.assertRaisesMessage(ImproperlyConfigured, "DJBRAINTREE_PAYER_MODEL must have an email attribute.", get_subscriber_model)

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.Organization')
    def test_no_callback(self):
        self.assertRaisesMessage(ImproperlyConfigured, "DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK must be implemented if a DJBRAINTREE_PAYER_MODEL is defined.", get_subscriber_model)

    @override_settings(DJBRAINTREE_PAYER_MODEL='testapp.Organization', DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK=5)
    def test_bad_callback(self):
        self.assertRaisesMessage(ImproperlyConfigured, "DJBRAINTREE_PAYER_MODEL_REQUEST_CALLBACK must be callable.", get_subscriber_model)


class TestSettings(TestCase):

    def test_plan_from_stripe_ID(self):
        plan = plan_from_stripe_id("test_id")
        self.assertEqual("test", plan)

    @override_settings(DJSTRIPE_PLANS={})
    def test_empty_plans(self):
        plan = plan_from_stripe_id("test_id")
        self.assertEqual(None, plan)
