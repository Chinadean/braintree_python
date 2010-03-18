from decimal import Decimal
from braintree.util.http import Http
from braintree.successful_result import SuccessfulResult
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.address import Address
from braintree.credit_card import CreditCard
from braintree.customer import Customer
from braintree.exceptions.not_found_error import NotFoundError

class Transaction(Resource):
    @staticmethod
    def credit(params={}):
        params["type"] = "credit"
        return Transaction.__create(params)

    @staticmethod
    def sale(params={}):
        params["type"] = "sale"
        return Transaction.__create(params)

    @staticmethod
    def __create(params):
        Resource.verify_keys(params, Transaction.create_signature())
        response = Http().post("/transactions", {"transaction": params})
        if "transaction" in response:
            return SuccessfulResult({"transaction": Transaction(response["transaction"])})
        elif "api_error_response" in response:
            return ErrorResult(response["api_error_response"])

    @staticmethod
    def create_signature():
        return [
            "amount", "customer_id", "order_id", "payment_method_token", "type",
            {
                "credit_card": [
                    "token", "cvv", "expiration_date", "number"
                ]
            },
            {
                "customer": [
                    "id", "company", "email", "fax", "first_name", "last_name", "phone", "website"
                ]
            },
            {
                "billing": [
                    "first_name", "last_name", "company", "country_name", "extended_address", "locality",
                    "postal_code", "region", "street_address"
                ]
            },
            {
                "shipping": [
                    "first_name", "last_name", "company", "country_name", "extended_address", "locality",
                    "postal_code", "region", "street_address"
                ]
            },
            {
                "options": [
                    "store_in_vault", "submit_for_settlement", "add_billing_address_to_payment_method",
                    "store_shipping_address_in_vault"
                ]
            },
            {"custom_fields": ["_any_key_"]}
        ]

    def __init__(self, attributes):
        if "billing" in attributes:
            attributes["billing_details"] = Address(attributes.pop("billing"))
        if "credit_card" in attributes:
            attributes["credit_card_details"] = CreditCard(attributes.pop("credit_card"))
        if "customer" in attributes:
            attributes["customer_details"] = Customer(attributes.pop("customer"))
        if "shipping" in attributes:
            attributes["shipping_details"] = Address(attributes.pop("shipping"))
        Resource.__init__(self, attributes)
        self.amount = Decimal(self.amount)

    @property
    def vault_billing_address(self):
        return Address.find(self.customer_details.id, self.billing_details.id)

    @property
    def vault_credit_card(self):
        return CreditCard.find(self.credit_card_details.token)

    @property
    def vault_customer(self):
        return Customer.find(self.customer_details.id)
