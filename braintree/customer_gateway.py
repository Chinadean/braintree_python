import braintree
from braintree.customer import Customer
from braintree.error_result import ErrorResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.ids_search import IdsSearch
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult
from braintree.transparent_redirect import TransparentRedirect

class CustomerGateway(object):
    def __init__(self, config):
        self.config = config

    def all(self):
        response = self.config.http().post("/customers/advanced_search_ids")
        return ResourceCollection(None, response, self.__fetch)

    def confirm_transparent_redirect(self, query_string):
        id = TransparentRedirect.parse_and_validate_query_string(query_string)["id"][0]
        return self._post("/customers/all/confirm_transparent_redirect_request", {"id": id})

    def create(self, params={}):
        Resource.verify_keys(params, Customer.create_signature())
        return self._post("/customers", {"customer": params})

    def delete(self, customer_id):
        self.config.http().delete("/customers/" + customer_id)
        return SuccessfulResult()

    def find(self, customer_id):
        try:
            response = self.config.http().get("/customers/" + customer_id)
            return Customer(response["customer"])
        except NotFoundError:
            raise NotFoundError("customer with id " + customer_id + " not found")

    def transparent_redirect_create_url(self):
        return self.config.base_merchant_url() + "/customers/all/create_via_transparent_redirect_request"

    def transparent_redirect_update_url(self):
        return self.config.base_merchant_url() + "/customers/all/update_via_transparent_redirect_request"

    def update(self, customer_id, params={}):
        Resource.verify_keys(params, Customer.update_signature())
        response = self.config.http().put("/customers/" + customer_id, {"customer": params})
        if "customer" in response:
            return SuccessfulResult({"customer": Customer(response["customer"])})
        elif "api_error_response" in response:
            return ErrorResult(response["api_error_response"])

    def __fetch(self, query, ids):
        criteria = {}
        criteria["ids"] = IdsSearch.ids.in_list(ids).to_param()
        response = self.config.http().post("/customers/advanced_search", {"search": criteria})
        return [Customer(item) for item in ResourceCollection._extract_as_array(response["customers"], "customer")]

    def _post(self, url, params={}):
        response = self.config.http().post(url, params)
        if "customer" in response:
            return SuccessfulResult({"customer": Customer(response["customer"])})
        elif "api_error_response" in response:
            return ErrorResult(response["api_error_response"])
        else:
            pass

