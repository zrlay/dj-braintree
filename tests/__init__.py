from string import lower

from braintree import BraintreeGateway, SuccessfulResult
from django.utils import timezone


FAKE_TRANSACTION = {
    "id": "ch_xxxxxxxxxxxx",
    "additional_processor_response": "",
    "amount": "9.95",
    "avs_error_response_code": "U",
    "avs_postal_code_response_code": "I",
    "avs_street_address_response_code": "I",
    "channel": "",
    "created_at": timezone.now(),
    "currency_iso_code": "USD",
    "cvv_response_code": "U",
    "customer_details": {
        "email": "customer@gmail.com",
        "id": "cus_xxxxxxxxxxxxxxx",
    },

    "descriptor": {
        "name": "",
        "phone": "",
        "url": "",
    },

    "disbursement_details": {
        "disbursement_date": None,
        "funds_held": "",
        "settlement_amount": None,
        "settlement_currency_exchange_rate": None,
        "settlement_currency_iso_code": "USD",
        "success": "",
    },

    "escrow_status": "",
    "gateway_rejection_reason": "",
    "merchant_account_id": "dj_merch_id",
    "order_id": "order_xxxxxxxx",
    "payment_instrument_type": "credit_card",

    "paypal_details": {
        "authorization_id": "",
        "capture_id": "",
        "payer_email": "",
        "payer_first_name": "",
        "payer_id": "",
        "payer_last_name": "",
        "payment_id": "",
        "refund_id": "",
        "seller_protection_status": "",
        "tax_id_type": "",
        "transaction_fee_amount": "",
        "transaction_fee_currency_iso_code": "",
        "token": "",
        "image_url": "",
    },

    "plan_id": "",
    "processor_authorization_code": "A",
    "processor_response_code": "100",
    "processor_response_text": "Good.",
    "processor_settlement_response_code": "",
    "processor_settlement_response_text": "",
    "purchase_order_number": "po_xxxxxxxx",
    "recurring": False,
    "refund_ids": "",
    "refunded_transaction_id": "",

    "risk_data": {
        "decision": "Not Evaluated",
        "id": "risk_xxxxxxxx",
    },

    "service_fee_amount": "1.00",
    "settlement_batch_id": "",
    "status": "authorized",
    "status_history": "",

    "subscription_details": {
        "billing_period_end_date": "",
        "billing_period_start_date": "",
    },

    "subscription_id": "",
    "tax_amount": "",
    "tax_exempt": False,

    "three_d_secure_info": {
        "enrolled": "U",
        "liability_shift_possible": False,
        "liability_shifted": False,
        "status": "yes",
    },

    "type": "sale",
    "updated_at": timezone.now(),
    "voice_referral_number": "",
}


def convert_to_fake_success_result(braintree_obj_cls, cls, mock_data):
    """ Mocks a successful result from Braintree API """
    bt_gateway = BraintreeGateway()
    object_name = lower(cls.braintree_api_name)
    gateway = getattr(bt_gateway, object_name)
    return SuccessfulResult({object_name: braintree_obj_cls(gateway, mock_data)})