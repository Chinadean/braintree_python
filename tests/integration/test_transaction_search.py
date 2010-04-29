from tests.test_helper import *

class TestTransactionSearch(unittest.TestCase):
    def test_basic_search_returns_some_results(self):
        collection = Transaction.search("411111")

        self.assertTrue(collection.approximate_size > 0)
        self.assertEquals("411111", collection.first.credit_card_details.bin)

    def test_basic_search_with_no_results(self):
        collection = Transaction.search("no_such_transactions_exists")
        self.assertEquals(0, collection.approximate_size)
        self.assertEquals([], [transaction for transaction in collection.items])

    def test_basic_search_can_iterate_over_the_entire_collection(self):
        collection = Transaction.search("411111")
        self.assertTrue(collection.approximate_size > 100)

        transaction_ids = [transaction.id for transaction in collection.items]
        self.assertEquals(collection.approximate_size, len(set(transaction_ids)))

    def test_basic_serach_all_statuses(self):
        self.assertTrue(TestHelper.includes_status(Transaction.search("authorizing"), Transaction.Status.Authorizing))
        self.assertTrue(TestHelper.includes_status(Transaction.search("authorized"), Transaction.Status.Authorized))
        self.assertTrue(TestHelper.includes_status(Transaction.search("gateway_rejected"), Transaction.Status.GatewayRejected))
        self.assertTrue(TestHelper.includes_status(Transaction.search("failed"), Transaction.Status.Failed))
        self.assertTrue(TestHelper.includes_status(Transaction.search("processor_declined"), Transaction.Status.ProcessorDeclined))
        self.assertTrue(TestHelper.includes_status(Transaction.search("settled"), Transaction.Status.Settled))
        self.assertTrue(TestHelper.includes_status(Transaction.search("settlement_failed"), Transaction.Status.SettlementFailed))
        self.assertTrue(TestHelper.includes_status(Transaction.search("submitted_for_settlement"), Transaction.Status.SubmittedForSettlement))
        self.assertTrue(TestHelper.includes_status(Transaction.search("unknown"), Transaction.Status.Unknown))
        self.assertTrue(TestHelper.includes_status(Transaction.search("voided"), Transaction.Status.Voided))

    def test_advanced_search_no_results(self):
        collection = Transaction.search([
            TransactionSearch.billing_first_name == "no_such_person"
        ])
        self.assertEquals(0, collection.approximate_size)

    def test_advanced_search_searches_all_text_fields_at_once(self):
        first_name = "Tim%s" % randint(1, 1000)
        token = "creditcard%s" % randint(1, 1000)
        customer_id = "customer%s" % randint(1, 1000)

        transaction = Transaction.sale({
            "amount": "1000.00",
            "credit_card": {
                "number": "4111111111111111",
                "expiration_date": "05/2012",
                "cardholder_name": "Tom Smith",
                "token": token,
            },
            "billing": {
                "company": "Braintree",
                "country_name": "United States of America",
                "extended_address": "Suite 123",
                "first_name": first_name,
                "last_name": "Smith",
                "locality": "Chicago",
                "postal_code": "12345",
                "region": "IL",
                "street_address": "123 Main St"
            },
            "customer": {
                "company": "Braintree",
                "email": "smith@example.com",
                "fax": "5551231234",
                "first_name": "Tom",
                "id": customer_id,
                "last_name": "Smith",
                "phone": "5551231234",
                "website": "http://example.com",
            },
            "options": {
                "store_in_vault": True
            },
            "order_id": "myorder",
            "shipping": {
                "company": "Braintree P.S.",
                "country_name": "Mexico",
                "extended_address": "Apt 456",
                "first_name": "Thomas",
                "last_name": "Smithy",
                "locality": "Braintree",
                "postal_code": "54321",
                "region": "MA",
                "street_address": "456 Road"
            }
        }).transaction

        collection = Transaction.search([
            TransactionSearch.billing_company == "Braintree",
            TransactionSearch.billing_country_name == "United States of America",
            TransactionSearch.billing_extended_address == "Suite 123",
            TransactionSearch.billing_first_name == first_name,
            TransactionSearch.billing_last_name == "Smith",
            TransactionSearch.billing_locality == "Chicago",
            TransactionSearch.billing_postal_code == "12345",
            TransactionSearch.billing_region == "IL",
            TransactionSearch.billing_street_address == "123 Main St",
            TransactionSearch.credit_card_cardholder_name == "Tom Smith",
            TransactionSearch.credit_card_expiration_date == "05/2012",
            TransactionSearch.credit_card_number == "4111111111111111",
            TransactionSearch.customer_company == "Braintree",
            TransactionSearch.customer_email == "smith@example.com",
            TransactionSearch.customer_fax == "5551231234",
            TransactionSearch.customer_first_name == "Tom",
            TransactionSearch.customer_id == customer_id,
            TransactionSearch.customer_last_name == "Smith",
            TransactionSearch.customer_phone == "5551231234",
            TransactionSearch.customer_website == "http://example.com",
            TransactionSearch.order_id == "myorder",
            TransactionSearch.payment_method_token == token,
            TransactionSearch.processor_authorization_code == transaction.processor_authorization_code,
            TransactionSearch.shipping_company == "Braintree P.S.",
            TransactionSearch.shipping_country_name == "Mexico",
            TransactionSearch.shipping_extended_address == "Apt 456",
            TransactionSearch.shipping_first_name == "Thomas",
            TransactionSearch.shipping_last_name == "Smithy",
            TransactionSearch.shipping_locality == "Braintree",
            TransactionSearch.shipping_postal_code == "54321",
            TransactionSearch.shipping_region == "MA",
            TransactionSearch.shipping_street_address == "456 Road",
            TransactionSearch.id == transaction.id
        ])

        self.assertEquals(1, collection.approximate_size)
        self.assertEquals(transaction.id, collection.first.id)
