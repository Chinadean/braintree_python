from braintree.resource import Resource
from braintree.configuration import Configuration
from braintree.subscription import Subscription

class WebhookNotification(Resource):
    class Kind(object):
        SubscriptionPastDue = "subscription_past_due"

    @staticmethod
    def parse(signature, payload):
        return Configuration.gateway().webhook_notification.parse(signature, payload)

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if "subscription" in attributes['subject']:
            self.subscription = Subscription(gateway, attributes['subject']['subscription'])
