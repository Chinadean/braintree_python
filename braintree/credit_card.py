from braintree.util.http import Http
from braintree.successful_result import SuccessfulResult
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.exceptions.argument_error import ArgumentError

class CreditCard(Resource):
    @staticmethod
    def create(params={}):
        # Resource.verify_keys(params, CreditCard.__create_signature())
        response = Http().post("/payment_methods", {"credit_card": params})
        if "credit_card" in response:
            return SuccessfulResult({"credit_card": CreditCard(response["credit_card"])})
        elif "api_error_response" in response:
            return ErrorResult(response["api_error_response"])
        else:
            pass

    def __init__(self, attributes):
        Resource.__init__(self, attributes)
        self.expiration_date = self.expiration_month + "/" + self.expiration_year

