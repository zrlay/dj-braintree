# -*- coding: utf-8 -*-
import warnings

from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from braintree.transaction import Transaction

VERIFICATION_CHOICES = [
    ("M", "Matches"),
    ("N", "Does not Match"),
    ("U", "Not Verified"),
    ("I", "Not Provided"),
    ("A", "Not Applicable"),
]

STATUS_CHOICES = [
(Transaction.Status.AuthorizationExpired, Transaction.Status.AuthorizationExpired),
(Transaction.Status.Authorized, Transaction.Status.Authorized),
(Transaction.Status.Authorizing, Transaction.Status.Authorizing),
(Transaction.Status.Failed, Transaction.Status.Failed),
(Transaction.Status.GatewayRejected, Transaction.Status.GatewayRejected),
(Transaction.Status.ProcessorDeclined, Transaction.Status.ProcessorDeclined),
(Transaction.Status.Settled, Transaction.Status.Settled),
(Transaction.Status.SettlementConfirmed, Transaction.Status.SettlementConfirmed),
(Transaction.Status.SettlementDeclined, Transaction.Status.SettlementDeclined),
(Transaction.Status.SettlementFailed, Transaction.Status.SettlementFailed),
(Transaction.Status.SettlementPending, Transaction.Status.SettlementPending),
(Transaction.Status.Settling, Transaction.Status.Settling),
(Transaction.Status.SubmittedForSettlement, Transaction.Status.SubmittedForSettlement),
(Transaction.Status.Voided, Transaction.Status.Voided),
(Transaction.Status.Unrecognized, Transaction.Status.Unrecognized),
]


THREE_D_SECURE_CHOICES = [
    ("Y", "Yes"),
    ("N", "No"),
    ("U", "Unavailable"),
    ("B", "Bypass"),
    ("E", "RequestFailure"),
]

ANONYMOUS_USER_ERROR_MSG = (
    "dj-braintree's payment checking mechanisms require the user "
    "be authenticated before use. Please use django.contrib.auth's "
    "login_required decorator or a LoginRequiredMixin. "
    "Please read the warning at "
    "http://dj-braintree.readthedocs.org/en/latest/usage.html#ongoing-subscriptions."
)

def entity_has_active_subscription(entity):
    """
    Helper function to check if an entity has an active subscription.
    Throws improperlyConfigured if the entity is an instance of AUTH_USER_MODEL
    and get_user_model().is_anonymous == True.

    Activate subscription rules (or):
        * customer has active subscription

    If the entity is an instance of AUTH_USER_MODEL, active subscription rules (or):
        * customer has active subscription
        * user.is_superuser
        * user.is_staff
    """
    from djbraintree.models import Customer

    if isinstance(entity, AnonymousUser):
        raise ImproperlyConfigured(ANONYMOUS_USER_ERROR_MSG)

    if isinstance(entity, get_user_model()):
        if entity.is_superuser or entity.is_staff:
            return True

    customer, created = Customer.get_or_create(entity)
    if created or not customer.has_active_subscription():
        return False
    return True


def get_supported_currency_choices(api_key):
    """
    Pulls a braintree account's supported currencies and returns a choices tuple of
    those supported currencies.

    :param api_key: The api key associated with the account from which to pull data.
    :type api_key: str
    """

    import stripe
    stripe.api_key = api_key

    account = stripe.Account.retrieve()
    return [(currency, currency.upper()) for currency in account["currencies_supported"]]
