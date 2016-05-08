Migrating to dj-braintree
======================

There are a number of other Django powered stripe apps. This document explains how to migrate from them to **dj-braintree**.

django-stripe-payments
----------------------

Most of the settings can be used as is, but with these exceptions:

PAYMENT_PLANS vs DJSTRIPE_PLANS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**dj-braintree** allows for plans with decimal numbers. So you can have plans that are $9.99 instead of just $10. The price in a specific plan is therefore in cents rather than whole dollars

.. code-block:: python

    # settings.py

    # django-stripe-payments way
    PAYMENT_PLANS = {
        "monthly": {
            "stripe_plan_id": "pro-monthly",
            "name": "Web App Pro ($25/month)",
            "description": "The monthly subscription plan to WebApp",
            "price": 25,  # $25.00
            "currency": "usd",
            "interval": "month"
        },
    }

    # dj-braintree way
    DJSTRIPE_PLANS = {
        "monthly": {
            "stripe_plan_id": "pro-monthly",
            "name": "Web App Pro ($24.99/month)",
            "description": "The monthly subscription plan to WebApp",
            "price": 2499,  # $24.99
            "currency": "usd",
            "interval": "month"
        },
    }

Migrating Settings
~~~~~~~~~~~~~~~~~~

TODO

Migrating Data
~~~~~~~~~~~~~~~

**Issues:**

1. **dj-braintree** includes South migrations and **django-stripe-payments** has no database migrations.
2. **dj-braintree** replaces the ``payments.models.StripeObject.created_at`` field with ``django-model-utils`` fields of ``model_utls.models.TimeStampedModel.created`` and ``model_utls.models.TimeStampedModel.modified``.

This will require some sort of one-time migration script. If you create one for your own project, please submit it or link to a paste/gist of the code.

.. seealso::

    * https://github.com/pydanny/dj-braintree/issues/10.

Migrating Templates
~~~~~~~~~~~~~~~~~~~~

**Issue: django-stripe-payments** uses Bootstrap 2 and django-forms-bootstrap, while **dj-braintree** uses Bootstrap 3 and eschews the use of Django form libraries in favor of hand-crafted forms.

TODO: Write this.

