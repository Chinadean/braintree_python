import unittest
import urllib
import httplib
from braintree.configuration import Configuration
from braintree.environment import Environment
from braintree.transparent_redirect import TransparentRedirect

Configuration.environment = Environment.DEVELOPMENT
Configuration.merchant_id = "integration_merchant_id"
Configuration.public_key = "integration_public_key"
Configuration.private_key = "integration_private_key"

class TestHelper(object):
    @staticmethod
    def create_via_tr(params, tr_data, url):
        return TestHelper.__post_form_data("POST", params, tr_data, url)

    @staticmethod
    def update_via_tr(params, tr_data, url):
        return TestHelper.__post_form_data("PUT", params, tr_data, url)

    @staticmethod
    def __post_form_data(http_verb, params, tr_data, url):
        params = TransparentRedirect.flatten_dictionary(params)
        params["tr_data"] = TransparentRedirect.tr_data(tr_data, "http://example.com/path/to/something?foo=bar")
        form_data = urllib.urlencode(params)

        if Configuration.is_ssl():
            connection_type = httplib.HTTPSConnection
        else:
            connection_type = httplib.HTTPConnection

        conn = connection_type(Configuration.server_and_port())
        conn.request(
            http_verb,
            url,
            form_data,
            TestHelper.__headers()
        )
        response = conn.getresponse()
        query_string = response.getheader('location').split("?", 1)[1]
        conn.close()
        return query_string

    @staticmethod
    def __headers():
        return {
            "Accept": "application/xml",
            "Content-type": "application/x-www-form-urlencoded",
        }

