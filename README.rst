=============================
dj-braintree
=============================
Django + Braintree Made Easy

Badges
------

.. image:: https://img.shields.io/travis/mightbejosh/dj-braintree.svg?style=flat-square
        :target: https://travis-ci.org/mightbejosh/dj-braintree
.. image:: https://img.shields.io/codecov/c/github/mightbejosh/dj-braintree/master.svg?style=flat-square
        :target: http://codecov.io/github/mightbejosh/dj-braintree?branch=master
.. image:: https://img.shields.io/requires/github/mightbejosh/dj-braintree.svg?style=flat-square
        :target: https://requires.io/github/mightbejosh/dj-braintree/requirements/?branch=master
.. image:: https://img.shields.io/codacy/3c99e13eda1c4dea9f993b362e4ea816.svg?style=flat-square
        :target: https://www.codacy.com/app/kavanaugh-development/dj-braintree/dashboard

.. image:: https://img.shields.io/pypi/v/dj-braintree.svg?style=flat-square
        :target: https://pypi.python.org/pypi/dj-braintree
.. image:: https://img.shields.io/pypi/dw/dj-braintree.svg?style=flat-square
        :target: https://pypi.python.org/pypi/dj-braintree

.. image:: https://img.shields.io/github/issues/mightbejosh/dj-braintree.svg?style=flat-square
        :target: https://github.com/mightbejosh/dj-braintree/issues
.. image:: https://img.shields.io/github/license/mightbejosh/dj-braintree.svg?style=flat-square
        :target: https://github.com/mightbejosh/dj-braintree/blob/master/LICENSE


Documentation
-------------

The full documentation is at http://dj-braintree.rtfd.org.

Features
--------

* Subscription management
* Single-unit purchases
* Works with Django ~=1.9.1, 1.8
* Works with Python 3.5, 3.4, 2.7
* Works with Bootstrap 3
* Built-in migrations
* Dead-Easy installation
* `djbraintree` namespace so you can have more than one payments related app
* Documented
* Tested
* Current API version (2012-11-07), in progress of being updated

Constraints
------------

1. For braintreepayments.com only
2. Support the Braintree Marketplace API (for creating ecommerce platforms, vendors and submerchants)
3. Only use or support well-maintained third-party libraries
4. For modern Python and Django


Quickstart
----------

Install dj-braintree:

.. code-block:: bash

    pip install dj-braintree

Add ``djbraintree`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS +=(
        "djbraintree",
    )

Add your Braintree keys:

.. code-block:: python

    BRAINTREE_PUBLIC_KEY = os.environ.get("BRAINTREE_PUBLIC_KEY", "<your publishable key>")
    BRAINTREE_PRIVATE_KEY = os.environ.get("BRAINTREE_PRIVATE_KEY", "<your secret key>")
    BRAINTREE_MERCHANT_ID = os.environ.get("BRAINTREE_MERCHANT_ID", "<your merchant ID>")

Add to the urls.py:

.. code-block:: python

    url(r'^payments/', include('djbraintree.urls', namespace="djbraintree")),

Run the commands::

    python manage.py migrate

    python manage.py djbraintree_init_customers

    python manage.py djbraintree_init_plans

If you haven't already, add JQuery and the Bootstrap 3.0.0+ JS and CSS to your base template:

.. code-block:: html

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">

    <!-- Optional theme -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap-theme.min.css">

    <!-- Latest JQuery (IE9+) -->
    <script src="//code.jquery.com/jquery-2.1.4.min.js"></script>

    <!-- Latest compiled and minified JavaScript -->
    <script src="//netdna.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>

Also, if you don't have it already, add a javascript block to your base.html file:

.. code-block:: html

    {% block javascript %}{% endblock %}


Running the Tests
-----------------

Assuming the tests are run against PostgreSQL::

    createdb djbraintree
    pip install -r requirements_test.txt
    python runtests.py

Follows Best Practices
======================

This project follows best practices as espoused in `Two Scoops of Django: Best Practices for Django 1.8`_.

.. _`Two Scoops of Django: Best Practices for Django 1.8`: http://twoscoopspress.org/products/two-scoops-of-django-1-8

Similar Projects
----------------

* https://github.com/pydanny/dj-stripe - The project after which dj-braintree is modeled. If you prefer Stripe to handle your payments, start here.
