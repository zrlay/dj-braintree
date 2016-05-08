from braintree import BraintreeGateway, SuccessfulResult


def convert_to_fake_success_result(cls, mock_data):
    """ Mocks a successful result from Braintree API """
    bt_gateway = BraintreeGateway()
    gateway = getattr(bt_gateway, cls.braintree_api_name)
    return SuccessfulResult({"merchant_account": cls(gateway, mock_data)})