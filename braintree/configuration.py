import os
from braintree.environment import Environment

class Configuration(object):
    @staticmethod
    def base_merchant_path():
        return "/merchants/" + Configuration.merchant_id

    @staticmethod
    def base_merchant_url():
        return Configuration.protocol() + Configuration.server_and_port() + Configuration.base_merchant_path()

    @staticmethod
    def server_and_port():
        config = Configuration()
        return config.server() + ":" + str(config.port())

    @staticmethod
    def is_ssl():
        if Configuration.environment == Environment.DEVELOPMENT:
            return False
        else:
            return True

    @staticmethod
    def protocol():
        if Configuration.is_ssl():
            return "https://"
        else:
            return "http://"

    def port(self):
        if Configuration.environment == Environment.DEVELOPMENT:
            port = os.getenv("GATEWAY_PORT")
            if port:
                return int(port)
            else:
                return 3000
        else:
            return 443

    def server(self):
        if Configuration.environment == Environment.DEVELOPMENT:
            return "localhost"
        elif Configuration.environment == Environment.PRODUCTION:
            return "www.braintreegateway.com"
        elif Configuration.environment == Environment.SANDBOX:
            return "sandbox.braintreegateway.com"
