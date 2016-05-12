import datetime
from braintree import BraintreeGateway as GWay
from braintree import SuccessfulResult
from braintree.transaction import Transaction as Tx


def get_fake_success_transaction(**kwargs):
    FAKE_TRANSACTION = {
        u'purchase_order_number': None,
        u'merchant_account_id': u'zacharylayng',
        u'updated_at': datetime.datetime(2016, 5, 11, 0, 0, 35),
        u'processor_response_code': u'1000',
        u'tax_exempt': False,
        u'processor_settlement_response_text': '',
        u'id': u'd5y99n',
        u'custom_fields': '',
        u'plan_id': None,
        u'billing': {
            u'first_name': None,
            u'last_name': None,
            u'country_code_alpha2': None,
            u'country_code_alpha3': None,
            u'extended_address': None,
            u'locality': None,
            u'company': None,
            u'country_code_numeric': None,
            u'postal_code': u'94107',
            u'country_name': None,
            u'region': None,
            u'id': None,
            u'street_address': None
        },
        u'discounts': [],
        u'refund_id': None,
        u'currency_iso_code': u'USD',
        u'cvv_response_code': u'M',
        u'add_ons': [],
        u'refunded_transaction_id': None,
        u'processor_settlement_response_code': '',
        u'subscription_id': None,
        u'type': u'sale',
        u'partial_settlement_transaction_ids': [],
        u'channel': None,
        u'status': u'authorized',
        u'avs_street_address_response_code': u'I',
        u'order_id': None,
        u'avs_error_response_code': None,
        u'sub_merchant_account_id': None,
        u'payment_instrument_type': u'credit_card',
        u'credit_card': {
            u'bin': u'378282',
            u'expiration_month': u'12',
            u'unique_number_identifier': None,
            u'prepaid': u'Unknown',
            u'expiration_year': u'2020',
            u'durbin_regulated': u'Unknown',
            u'payroll': u'Unknown',
            u'debit': u'Unknown',
            u'commercial': u'Unknown',
            u'issuing_bank': u'Unknown',
            u'last_4': u'0005',
            u'card_type': u'American Express',
            u'cardholder_name': None,
            u'token': None,
            u'customer_location': u'US',
            u'image_url': u'https://assets.braintreegateway.com/payment_method_logo/american_express.png?environment=sandbox',
            u'country_of_issuance': u'Unknown',
            u'healthcare': u'Unknown',
            u'venmo_sdk': False,
            u'product_id': u'Unknown'
        },
        u'refund_ids': [],
        u'service_fee_amount': None,
        u'processor_authorization_code': u'2TPFML',
        u'additional_processor_response': None,
        u'escrow_status': None,
        u'authorized_transaction_id': None,
        u'three_d_secure_info': None,
        u'subscription': {
            u'billing_period_start_date': None,
            u'billing_period_end_date': None
        },
        u'customer': {
            u'website': None,
            u'first_name': None,
            u'last_name': None,
            u'company': None,
            u'fax': None,
            u'email': None,
            u'phone': None,
            u'id': None
        },
        u'tax_amount': None,
        u'settlement_batch_id': None,
        u'recurring': False,
        u'created_at': datetime.datetime(2016, 5, 11, 0, 0, 35),
        u'processor_response_text': u'Approved',
        u'avs_postal_code_response_code': u'M',
        u'shipping': {
            u'first_name': None,
            u'last_name': None,
            u'country_code_alpha2': None,
            u'country_code_alpha3': None,
            u'extended_address': None,
            u'locality': None,
            u'company': None,
            u'country_code_numeric': None,
            u'postal_code': None,
            u'country_name': None,
            u'region': None,
            u'id': None,
            u'street_address': None
        },
        u'status_history': [
            {
                u'status': u'authorized',
                u'timestamp': datetime.datetime(2016, 5, 11, 0, 0, 35),
                u'amount': u'10.00',
                u'user': u'mightbejosh@gmail.com',
                u'transaction_source': u'api'
            }
        ],
        u'disbursement_details': {
            u'settlement_currency_exchange_rate': None,
            u'success': None,
            u'disbursement_date': None,
            u'settlement_amount': None,
            u'settlement_currency_iso_code': None,
            u'funds_held': None
        },
        u'descriptor': {
            u'url': None,
            u'phone': None,
            u'name': None
        },
        u'amount': u'10.00',
        u'disputes': [],
        u'gateway_rejection_reason': None,
        u'voice_referral_number': None,
        u'master_merchant_account_id': None
    }
    FAKE_TRANSACTION.update(kwargs)

    return SuccessfulResult(
        {"transaction": Tx(GWay(), FAKE_TRANSACTION)})
