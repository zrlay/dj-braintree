# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import decimal

from django.db import models


class BraintreeObjectManager(models.Manager):

    def exists_by_json(self, data):
        """
        Search for a matching braintree object based on a Braintree object
        received from Braintree in JSON format

        :param data: Braintree object parsed from a JSON string into an object
        :type data: dict
        :rtype: bool
        :returns: True if the requested object exists, False otherwise
        """
        return self.filter(braintree_id=data["id"]).exists()

    def get_by_json(self, data, field_name="id"):
        """
        Retrieve a matching braintree object based on a Braintree object
        received from Braintree in JSON format
        :param data: Braintree event object parsed from a JSON string into an object
        :type data: dict
        """
        return self.get(braintree_id=data[field_name])