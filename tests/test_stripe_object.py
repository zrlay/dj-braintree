"""
.. module:: dj-braintree.tests.test_braintree_object
   :synopsis: dj-braintree BraintreeObject Model Tests.

.. moduleauthor:: Bill Huneke (@wahuneke)

"""

from django.test import TestCase

from djbraintree.braintree_objects import BraintreeObject


class BraintreeObjectExceptionsTest(TestCase):
    def test_missing_apiname(self):
        # This class fails to provide a braintree_api_name attribute
        class MissingApiName(BraintreeObject):
            pass

        with self.assertRaises(NotImplementedError):
            MissingApiName.api()

    def test_missing_obj_to_record(self):
        # This class fails to provide a braintree_api_name attribute
        class MissingObjToRecord(BraintreeObject):
            braintree_api_name = "hello"

        with self.assertRaises(NotImplementedError):
            MissingObjToRecord.create_from_braintree_object({})

