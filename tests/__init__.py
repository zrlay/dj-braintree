from string import lower

from braintree import BraintreeGateway, SuccessfulResult


def convert_to_fake_success_result(braintree_obj_cls, cls, mock_data):
    """ Mocks a successful result from Braintree API """
    bt_gateway = BraintreeGateway()
    object_name = lower(cls.braintree_api_name)
    gateway = getattr(bt_gateway, object_name)
    return SuccessfulResult({object_name: braintree_obj_cls(gateway, mock_data)})