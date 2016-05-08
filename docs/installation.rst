============
Installation
============

Get the distribution
---------------------

At the command line::

    $ pip install dj-braintree

Or, if you have virtualenvwrapper installed::

    $ mkvirtualenv dj-braintree
    $ pip install dj-braintree

Or, if you want to develop on ``djbraintree`` itself::

    $ git clone https://github.com/<yourname>/dj-braintree/
    $ python setup.py develop


Configuration
---------------


Add ``djbraintree`` to your ``INSTALLED_APPS``:

.. code-block:: python

    INSTALLED_APPS += (
        "djbraintree",
    )

Add your stripe keys:

.. code-block:: python

    BRAINTREE_PUBLIC_KEY = os.environ.get("BRAINTREE_PUBLIC_KEY", "<your publishable key>")
    BRAINTREE_PRIVATE_KEY = os.environ.get("BRAINTREE_PRIVATE_KEY", "<your secret key>")

Add some payment plans:

.. code-block:: python

    DJSTRIPE_PLANS = {
        "monthly": {
            "stripe_plan_id": "pro-monthly",
            "name": "Web App Pro ($25/month)",
            "description": "The monthly subscription plan to WebApp",
            "price": 2500,  # $25.00
            "currency": "usd",
            "interval": "month"
        },
        "yearly": {
            "stripe_plan_id": "pro-yearly",
            "name": "Web App Pro ($199/year)",
            "description": "The annual subscription plan to WebApp",
            "price": 19900,  # $199.00
            "currency": "usd",
            "interval": "year"
        }
    }

.. note:: Braintree Plan creation

    Not all properties listed in the plans above are used by Braintree - i.e 'description', which
    is used to display the plans description within specific templates.

    Although any arbitrary property you require can be added to each plan listed in DJ_STRIPE_PLANS,
    only specific properties are used by Braintree. The full list of required and optional arguments
    can be found here_.

.. _here: https://stripe.com/docs/api/python#create_plan

.. note:: The display order of the plans

    If you prefer the plans to appear (in views) in the order given in the
    `DJSTRIPE_PLANS` setting, use an `OrderedDict` from the `collections`
    module in the standard library, rather than an ordinary dict.

Add to the urls.py::

    url(r'^payments/', include('djbraintree.urls', namespace="djbraintree")),

Run the commands::

    python manage.py migrate

    python manage.py djbraintree_init_customers

    python manage.py djbraintree_init_plans

If you haven't already, add JQuery and the Bootstrap 3.0.0+ JS and CSS to your base template:

.. code-block:: html

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="https://netdna.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css">

    <!-- Optional theme -->
    <link rel="stylesheet" href="https://netdna.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap-theme.min.css">

    <!-- Latest JQuery (IE9+) -->
    <script src="//code.jquery.com/jquery-2.1.4.min.js"></script>

    <!-- Latest compiled and minified JavaScript -->
    <script src="https://netdna.bootstrapcdn.com/bootstrap/3.3.4/js/bootstrap.min.js"></script>

Also, if you don't have it already, add a javascript block to your base.html file:

.. code-block:: html

    {% block javascript %}{% endblock %}


Running Tests
--------------

Assuming the tests are run against PostgreSQL::

    createdb djbraintree
    pip install -r requirements_test.txt
    python runtests.py
