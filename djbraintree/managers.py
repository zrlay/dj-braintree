# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import models


class BraintreeObjectManager(models.Manager):

    def exists_by_json(self, braintree_object):
        """
        Search for a matching braintree object based on a Braintree object
        received from Braintree in JSON format

        :param braintree_object: Braintree object parsed from a JSON string into an object
        :type data: dict
        :rtype: bool
        :returns: True if the requested object exists, False otherwise
        """
        return self.filter(braintree_id=braintree_object.id).exists()

    def get_by_resource(self, braintree_object):
        """
        Retrieve a local BraintreeObject based on a response resource object

        :param braintree_object: A braintree response resource
        :type braintree_object: braintree.Resource
        """
        try:
            return self.get(braintree_id=braintree_object.id)
        except AttributeError:
            # If the braintree_object doesnt have an ID,
            # it doesn't exist on braintree, so what record are we fetching?
            # (The braintree python SDK can produce "empty" resources).
            raise self.model.DoesNotExist
