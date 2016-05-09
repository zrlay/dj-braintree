# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import decimal

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

    def get_by_json(self, braintree_object_id):
        """
        Retrieve a matching braintree object based on a Braintree object
        received from Braintree
        :param braintree_object_id: Braintree_id from Braintree Object
        :type braintree_object_id: string
        """
        return self.get(braintree_id=braintree_object_id)