from tests.test_helper import *

class TestSubscription(unittest.TestCase):
    def setUp(self):
        self.credit_card = Customer.create({
            "first_name": "Mike",
            "last_name": "Jones",
            "credit_card": {
                "number": "4111111111111111",
                "expiration_date": "05/2010",
                "cvv": "100"
            }
        }).customer.credit_cards[0]

        self.updateable_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "price": Decimal("54.32"),
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription


    def test_create_returns_successful_result_if_valid(self):
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        })

        self.assertTrue(result.is_success)
        subscription = result.subscription
        self.assertNotEquals(None, re.search("\A\w{6}\Z", subscription.id))
        self.assertEquals(Subscription.Status.Active, subscription.status)
        self.assertEquals("integration_trialless_plan", subscription.plan_id)
        self.assertEquals(TestHelper.default_merchant_account_id, subscription.merchant_account_id)

        self.assertEquals(date, type(subscription.first_billing_date))
        self.assertEquals(date, type(subscription.next_billing_date))
        self.assertEquals(date, type(subscription.billing_period_start_date))
        self.assertEquals(date, type(subscription.billing_period_end_date))

        self.assertEquals(0, subscription.failure_count)
        self.assertEquals(self.credit_card.token, subscription.payment_method_token)

    def test_create_can_set_the_id(self):
        new_id = str(random.randint(1, 1000000))
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"],
            "id": new_id
        })

        self.assertTrue(result.is_success)
        self.assertEquals(new_id, result.subscription.id)

    def test_create_can_set_the_merchant_account_id(self):
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"],
            "merchant_account_id": TestHelper.non_default_merchant_account_id
        })

        self.assertTrue(result.is_success)
        self.assertEquals(TestHelper.non_default_merchant_account_id, result.subscription.merchant_account_id)

    def test_create_defaults_to_plan_without_trial(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"],
        }).subscription

        self.assertEquals(TestHelper.trialless_plan["trial_period"], subscription.trial_period)
        self.assertEquals(None, subscription.trial_duration)
        self.assertEquals(None, subscription.trial_duration_unit)

    def test_create_defaults_to_plan_with_trial(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
        }).subscription

        self.assertEquals(TestHelper.trial_plan["trial_period"], subscription.trial_period)
        self.assertEquals(TestHelper.trial_plan["trial_duration"], subscription.trial_duration)
        self.assertEquals(TestHelper.trial_plan["trial_duration_unit"], subscription.trial_duration_unit)

    def test_create_and_override_plan_with_trial(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
            "trial_duration": 5,
            "trial_duration_unit": Subscription.TrialDurationUnit.Month
        }).subscription

        self.assertEquals(True, subscription.trial_period)
        self.assertEquals(5, subscription.trial_duration)
        self.assertEquals(Subscription.TrialDurationUnit.Month, subscription.trial_duration_unit)

    def test_create_and_override_trial_period(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
            "trial_period": False
        }).subscription

        self.assertEquals(False, subscription.trial_period)

    def test_create_and_override_number_of_billing_cycles(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
            "number_of_billing_cycles": 10
        }).subscription

        self.assertEquals(10, subscription.number_of_billing_cycles)

    def test_create_and_override_number_of_billing_cycles_to_never_expire(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
            "never_expires": True
        }).subscription

        self.assertEquals(None, subscription.number_of_billing_cycles)

    def test_create_creates_a_transaction_if_no_trial_period(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"],
        }).subscription

        self.assertEquals(1, len(subscription.transactions))
        transaction = subscription.transactions[0]
        self.assertEquals(Transaction, type(transaction))
        self.assertEquals(TestHelper.trialless_plan["price"], transaction.amount)
        self.assertEquals("sale", transaction.type)
        self.assertEquals(subscription.id, transaction.subscription_id)

    def test_create_returns_a_transaction_if_transaction_is_declined(self):
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"],
            "price": TransactionAmounts.Decline
        })

        self.assertFalse(result.is_success)
        self.assertEquals(Transaction.Status.ProcessorDeclined, result.transaction.status)

    def test_create_doesnt_creates_a_transaction_if_trial_period(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
        }).subscription

        self.assertEquals(0, len(subscription.transactions))

    def test_create_with_error_result(self):
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
            "id": "invalid token"
        })

        self.assertFalse(result.is_success)
        self.assertEquals("81906", result.errors.for_object("subscription").on("id")[0].code)

    def test_create_does_not_inherit_add_ons_or_discounts_from_the_plan_when_flag_is_set(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "options": {
                "do_not_inherit_add_ons_or_discounts": True
            }
        }).subscription

        self.assertEquals(0, len(subscription.add_ons))
        self.assertEquals(0, len(subscription.discounts))

    def test_create_inherits_add_ons_and_discounts_from_the_plan_when_not_specified(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"]
        }).subscription

        self.assertEquals(2, len(subscription.add_ons))
        add_ons = sorted(subscription.add_ons, key=lambda add_on: add_on.id)

        self.assertEquals("increase_10", add_ons[0].id)
        self.assertEquals(Decimal("10.00"), add_ons[0].amount)
        self.assertEquals(1, add_ons[0].quantity)
        self.assertEquals(None, add_ons[0].number_of_billing_cycles)
        self.assertTrue(add_ons[0].never_expires)

        self.assertEquals("increase_20", add_ons[1].id)
        self.assertEquals(Decimal("20.00"), add_ons[1].amount)
        self.assertEquals(1, add_ons[1].quantity)
        self.assertEquals(None, add_ons[1].number_of_billing_cycles)
        self.assertTrue(add_ons[1].never_expires)

        self.assertEquals(2, len(subscription.discounts))
        discounts = sorted(subscription.discounts, key=lambda discount: discount.id)

        self.assertEquals("discount_11", discounts[0].id)
        self.assertEquals(Decimal("11.00"), discounts[0].amount)
        self.assertEquals(1, discounts[0].quantity)
        self.assertEquals(None, discounts[0].number_of_billing_cycles)
        self.assertTrue(discounts[0].never_expires)

        self.assertEquals("discount_7", discounts[1].id)
        self.assertEquals(Decimal("7.00"), discounts[1].amount)
        self.assertEquals(1, discounts[1].quantity)
        self.assertEquals(None, discounts[1].number_of_billing_cycles)
        self.assertTrue(discounts[1].never_expires)

    def test_create_allows_overriding_of_inherited_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "update": [
                    {
                        "amount": Decimal("50.00"),
                        "existing_id": "increase_10",
                        "quantity": 2,
                        "number_of_billing_cycles": 5
                    },
                    {
                        "amount": Decimal("100.00"),
                        "existing_id": "increase_20",
                        "quantity": 4,
                        "never_expires": True
                    }
                ]
            },
            "discounts": {
                "update": [
                    {
                        "amount": Decimal("15.00"),
                        "existing_id": "discount_7",
                        "quantity": 3,
                        "number_of_billing_cycles": 19
                    }
                ]
            }
        }).subscription

        self.assertEquals(2, len(subscription.add_ons))
        add_ons = sorted(subscription.add_ons, key=lambda add_on: add_on.id)

        self.assertEquals("increase_10", add_ons[0].id)
        self.assertEquals(Decimal("50.00"), add_ons[0].amount)
        self.assertEquals(2, add_ons[0].quantity)
        self.assertEquals(5, add_ons[0].number_of_billing_cycles)
        self.assertFalse(add_ons[0].never_expires)

        self.assertEquals("increase_20", add_ons[1].id)
        self.assertEquals(Decimal("100.00"), add_ons[1].amount)
        self.assertEquals(4, add_ons[1].quantity)
        self.assertEquals(None, add_ons[1].number_of_billing_cycles)
        self.assertTrue(add_ons[1].never_expires)

        self.assertEquals(2, len(subscription.discounts))
        discounts = sorted(subscription.discounts, key=lambda discount: discount.id)

        self.assertEquals("discount_11", discounts[0].id)
        self.assertEquals(Decimal("11.00"), discounts[0].amount)
        self.assertEquals(1, discounts[0].quantity)
        self.assertEquals(None, discounts[0].number_of_billing_cycles)
        self.assertTrue(discounts[0].never_expires)

        self.assertEquals("discount_7", discounts[1].id)
        self.assertEquals(Decimal("15.00"), discounts[1].amount)
        self.assertEquals(3, discounts[1].quantity)
        self.assertEquals(19, discounts[1].number_of_billing_cycles)
        self.assertFalse(discounts[1].never_expires)

    def test_create_allows_deleting_of_inherited_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "remove": ["increase_10", "increase_20"]
            },
            "discounts": {
                "remove": ["discount_7"]
            }
        }).subscription

        self.assertEquals(0, len(subscription.add_ons))

        self.assertEquals(1, len(subscription.discounts))
        self.assertEquals("discount_11", subscription.discounts[0].id)

    def test_create_allows_adding_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "add": [
                    {
                        "amount": Decimal("50.00"),
                        "inherited_from_id": "increase_30",
                        "quantity": 2,
                        "number_of_billing_cycles": 5
                    }
                ],
                "remove": ["increase_10", "increase_20"]
            },
            "discounts": {
                "add": [
                    {
                        "amount": Decimal("17.00"),
                        "inherited_from_id": "discount_15",
                        "never_expires": True
                    }
                ],
                "remove": ["discount_7", "discount_11"]
            }
        }).subscription

        self.assertEquals(1, len(subscription.add_ons))

        self.assertEquals("increase_30", subscription.add_ons[0].id)
        self.assertEquals(Decimal("50.00"), subscription.add_ons[0].amount)
        self.assertEquals(2, subscription.add_ons[0].quantity)
        self.assertEquals(5, subscription.add_ons[0].number_of_billing_cycles)
        self.assertFalse(subscription.add_ons[0].never_expires)

        self.assertEquals(1, len(subscription.discounts))

        self.assertEquals("discount_15", subscription.discounts[0].id)
        self.assertEquals(Decimal("17.00"), subscription.discounts[0].amount)
        self.assertEquals(1, subscription.discounts[0].quantity)
        self.assertEquals(None, subscription.discounts[0].number_of_billing_cycles)
        self.assertTrue(subscription.discounts[0].never_expires)

    def test_create_properly_parses_validation_errors_for_arrays(self):
        result = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "update": [
                    {
                        "existing_id": "increase_10",
                        "amount": "invalid"
                    },
                    {
                        "existing_id": "increase_20",
                        "quantity": -2
                    }
                ]
            }
        })

        self.assertFalse(result.is_success)

        self.assertEquals(
            ErrorCodes.Subscription.Modification.AmountIsInvalid,
            result.errors.for_object("subscription").for_object("add_ons").for_object("update").for_index(0).on("amount")[0].code
        )
        self.assertEquals(
            ErrorCodes.Subscription.Modification.QuantityIsInvalid,
            result.errors.for_object("subscription").for_object("add_ons").for_object("update").for_index(1).on("quantity")[0].code
        )

    def test_find_with_valid_id(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"],
        }).subscription

        found_subscription = Subscription.find(subscription.id)
        self.assertEquals(subscription.id, found_subscription.id)

    def test_find_with_invalid_token(self):
        try:
            Subscription.find("bad_token")
            self.assertTrue(False)
        except Exception, e:
            self.assertEquals("subscription with id bad_token not found", str(e))

    def test_update_creates_a_prorated_transaction_when_merchant_is_set_to_prorate(self):
        new_id = str(random.randint(1, 1000000))
        result = Subscription.update(self.updateable_subscription.id, {
            "price": self.updateable_subscription.price + Decimal("1"),
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(2, len(subscription.transactions))

    def test_update_creates_a_prorated_transaction_when_flag_is_passed_as_True(self):
        new_id = str(random.randint(1, 1000000))
        result = Subscription.update(self.updateable_subscription.id, {
            "price": self.updateable_subscription.price + Decimal("1"),
            "options": {
                "prorate_charges": True
            }
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(2, len(subscription.transactions))

    def test_update_does_not_create_a_prorated_transaction_when_flag_is_passed_as_False(self):
        new_id = str(random.randint(1, 1000000))
        result = Subscription.update(self.updateable_subscription.id, {
            "price": self.updateable_subscription.price + Decimal("1"),
            "options": {
                "prorate_charges": False
            }
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(1, len(subscription.transactions))

    def test_update_with_successful_result(self):
        new_id = str(random.randint(1, 1000000))
        result = Subscription.update(self.updateable_subscription.id, {
            "id": new_id,
            "price": Decimal("9999.88"),
            "plan_id": TestHelper.trial_plan["id"]
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(new_id, subscription.id)
        self.assertEquals(TestHelper.trial_plan["id"], subscription.plan_id)
        self.assertEquals(Decimal("9999.88"), subscription.price)

    def test_update_with_merchant_account_id(self):
        result = Subscription.update(self.updateable_subscription.id, {
            "merchant_account_id": TestHelper.non_default_merchant_account_id,
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(TestHelper.non_default_merchant_account_id, subscription.merchant_account_id)

    def test_update_with_payment_method_token(self):
        newCard = CreditCard.create({
            "customer_id": self.credit_card.customer_id,
            "number": "4111111111111111",
            "expiration_date": "05/2009",
            "cvv": "100",
            "cardholder_name": self.credit_card.cardholder_name
        }).credit_card

        result = Subscription.update(self.updateable_subscription.id, {
            "payment_method_token": newCard.token
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(newCard.token, subscription.payment_method_token)

    def test_update_with_number_of_billing_cycles(self):
        result = Subscription.update(self.updateable_subscription.id, {
            "number_of_billing_cycles": 10
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(10, subscription.number_of_billing_cycles)

    def test_update_with_never_expires(self):
        result = Subscription.update(self.updateable_subscription.id, {
            "never_expires": True
        })

        self.assertTrue(result.is_success)

        subscription = result.subscription
        self.assertEquals(None, subscription.number_of_billing_cycles)

    def test_update_with_error_result(self):
        result = Subscription.update(self.updateable_subscription.id, {
            "id": "bad id",
        })

        self.assertFalse(result.is_success)
        self.assertEquals("81906", result.errors.for_object("subscription").on("id")[0].code)

    @raises(NotFoundError)
    def test_update_raises_error_when_subscription_not_found(self):
        Subscription.update("notfound", {
            "id": "newid",
        })

    def test_update_allows_overriding_of_inherited_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
        }).subscription

        subscription = Subscription.update(subscription.id, {
            "add_ons": {
                "update": [
                    {
                        "amount": Decimal("50.00"),
                        "existing_id": "increase_10",
                        "quantity": 2,
                        "number_of_billing_cycles": 5
                    },
                    {
                        "amount": Decimal("100.00"),
                        "existing_id": "increase_20",
                        "quantity": 4,
                        "never_expires": True
                    }
                ]
            },
            "discounts": {
                "update": [
                    {
                        "amount": Decimal("15.00"),
                        "existing_id": "discount_7",
                        "quantity": 3,
                        "number_of_billing_cycles": 19
                    }
                ]
            }
        }).subscription

        self.assertEquals(2, len(subscription.add_ons))
        add_ons = sorted(subscription.add_ons, key=lambda add_on: add_on.id)

        self.assertEquals("increase_10", add_ons[0].id)
        self.assertEquals(Decimal("50.00"), add_ons[0].amount)
        self.assertEquals(2, add_ons[0].quantity)
        self.assertEquals(5, add_ons[0].number_of_billing_cycles)
        self.assertFalse(add_ons[0].never_expires)

        self.assertEquals("increase_20", add_ons[1].id)
        self.assertEquals(Decimal("100.00"), add_ons[1].amount)
        self.assertEquals(4, add_ons[1].quantity)
        self.assertEquals(None, add_ons[1].number_of_billing_cycles)
        self.assertTrue(add_ons[1].never_expires)

        self.assertEquals(2, len(subscription.discounts))
        discounts = sorted(subscription.discounts, key=lambda discount: discount.id)

        self.assertEquals("discount_11", discounts[0].id)
        self.assertEquals(Decimal("11.00"), discounts[0].amount)
        self.assertEquals(1, discounts[0].quantity)
        self.assertEquals(None, discounts[0].number_of_billing_cycles)
        self.assertTrue(discounts[0].never_expires)

        self.assertEquals("discount_7", discounts[1].id)
        self.assertEquals(Decimal("15.00"), discounts[1].amount)
        self.assertEquals(3, discounts[1].quantity)
        self.assertEquals(19, discounts[1].number_of_billing_cycles)
        self.assertFalse(discounts[1].never_expires)

    def test_update_allows_adding_and_removing_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
        }).subscription

        subscription = Subscription.update(subscription.id, {
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "add": [
                    {
                        "amount": Decimal("50.00"),
                        "inherited_from_id": "increase_30",
                        "quantity": 2,
                        "number_of_billing_cycles": 5
                    }
                ],
                "remove": ["increase_10", "increase_20"]
            },
            "discounts": {
                "add": [
                    {
                        "amount": Decimal("17.00"),
                        "inherited_from_id": "discount_15",
                        "never_expires": True
                    }
                ],
                "remove": ["discount_7", "discount_11"]
            }
        }).subscription

        self.assertEquals(1, len(subscription.add_ons))

        self.assertEquals("increase_30", subscription.add_ons[0].id)
        self.assertEquals(Decimal("50.00"), subscription.add_ons[0].amount)
        self.assertEquals(2, subscription.add_ons[0].quantity)
        self.assertEquals(5, subscription.add_ons[0].number_of_billing_cycles)
        self.assertFalse(subscription.add_ons[0].never_expires)

        self.assertEquals(1, len(subscription.discounts))

        self.assertEquals("discount_15", subscription.discounts[0].id)
        self.assertEquals(Decimal("17.00"), subscription.discounts[0].amount)
        self.assertEquals(1, subscription.discounts[0].quantity)
        self.assertEquals(None, subscription.discounts[0].number_of_billing_cycles)
        self.assertTrue(subscription.discounts[0].never_expires)

    def test_update_can_replace_entire_set_of_add_ons_and_discounts(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
        }).subscription

        subscription = Subscription.update(subscription.id, {
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.add_on_discount_plan["id"],
            "add_ons": {
                "add": [
                    { "inherited_from_id": "increase_30", },
                    { "inherited_from_id": "increase_20", }
                ]
            },
            "discounts": {
                "add": [
                    { "inherited_from_id": "discount_15", }
                ]
            },
            "options": {
                "replace_all_add_ons_and_discounts": True
            }
        }).subscription

        self.assertEquals(2, len(subscription.add_ons))
        add_ons = sorted(subscription.add_ons, key=lambda add_on: add_on.id)

        self.assertEquals("increase_20", add_ons[0].id)
        self.assertEquals(Decimal("20.00"), add_ons[0].amount)
        self.assertEquals(1, add_ons[0].quantity)
        self.assertEquals(None, add_ons[0].number_of_billing_cycles)
        self.assertTrue(add_ons[0].never_expires)

        self.assertEquals("increase_30", add_ons[1].id)
        self.assertEquals(Decimal("30.00"), add_ons[1].amount)
        self.assertEquals(1, add_ons[1].quantity)
        self.assertEquals(None, add_ons[1].number_of_billing_cycles)
        self.assertTrue(add_ons[1].never_expires)

        self.assertEquals(1, len(subscription.discounts))

        self.assertEquals("discount_15", subscription.discounts[0].id)
        self.assertEquals(Decimal("15.00"), subscription.discounts[0].amount)
        self.assertEquals(1, subscription.discounts[0].quantity)
        self.assertEquals(None, subscription.discounts[0].number_of_billing_cycles)
        self.assertTrue(subscription.discounts[0].never_expires)

    def test_cancel_with_successful_response(self):
        subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription

        result = Subscription.cancel(subscription.id)
        self.assertTrue(result.is_success)
        self.assertEqual("Canceled", result.subscription.status)

    def test_unsuccessful_cancel_returns_validation_error(self):
        Subscription.cancel(self.updateable_subscription.id)
        result = Subscription.cancel(self.updateable_subscription.id)

        self.assertFalse(result.is_success)
        self.assertEquals("81905", result.errors.for_object("subscription").on("status")[0].code)

    @raises(NotFoundError)
    def test_cancel_raises_not_found_error_with_bad_subscription(self):
        Subscription.cancel("notreal")

    def test_search_with_argument_list_rather_than_literal_list(self):
        trial_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"]
        }).subscription

        trialless_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription

        collection = Subscription.search(
            SubscriptionSearch.plan_id == "integration_trial_plan"
        )

        self.assertTrue(TestHelper.includes(collection, trial_subscription))
        self.assertFalse(TestHelper.includes(collection, trialless_subscription))

    def test_search_on_plan_id(self):
        trial_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trial_plan["id"]
        }).subscription

        trialless_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription

        collection = Subscription.search([
            SubscriptionSearch.plan_id == "integration_trial_plan"
        ])

        self.assertTrue(TestHelper.includes(collection, trial_subscription))
        self.assertFalse(TestHelper.includes(collection, trialless_subscription))

    def test_search_on_status(self):
        active_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription

        canceled_subscription = Subscription.create({
            "payment_method_token": self.credit_card.token,
            "plan_id": TestHelper.trialless_plan["id"]
        }).subscription
        Subscription.cancel(canceled_subscription.id)

        collection = Subscription.search([
            SubscriptionSearch.status.in_list([Subscription.Status.Active, Subscription.Status.Canceled])
        ])

        self.assertTrue(TestHelper.includes(collection, active_subscription))
        self.assertTrue(TestHelper.includes(collection, canceled_subscription))

    def test_retryCharge_without_amount__deprecated(self):
        subscription = Subscription.search([
            SubscriptionSearch.status.in_list([Subscription.Status.PastDue])
        ]).first

        result = Subscription.retryCharge(subscription.id);

        self.assertTrue(result.is_success);
        transaction = result.transaction;

        self.assertEquals(subscription.price, transaction.amount);
        self.assertNotEqual(None, transaction.processor_authorization_code);
        self.assertEquals(Transaction.Type.Sale, transaction.type);
        self.assertEquals(Transaction.Status.Authorized, transaction.status);

    def test_retry_charge_without_amount(self):
        subscription = Subscription.search([
            SubscriptionSearch.status.in_list([Subscription.Status.PastDue])
        ]).first

        result = Subscription.retry_charge(subscription.id);

        self.assertTrue(result.is_success);
        transaction = result.transaction;

        self.assertEquals(subscription.price, transaction.amount);
        self.assertNotEqual(None, transaction.processor_authorization_code);
        self.assertEquals(Transaction.Type.Sale, transaction.type);
        self.assertEquals(Transaction.Status.Authorized, transaction.status);

    def test_retryCharge_with_amount__deprecated(self):
        subscription = Subscription.search([
            SubscriptionSearch.status.in_list([Subscription.Status.PastDue])
        ]).first

        result = Subscription.retryCharge(subscription.id, Decimal(TransactionAmounts.Authorize));

        self.assertTrue(result.is_success);
        transaction = result.transaction;

        self.assertEquals(Decimal(TransactionAmounts.Authorize), transaction.amount);
        self.assertNotEqual(None, transaction.processor_authorization_code);
        self.assertEquals(Transaction.Type.Sale, transaction.type);
        self.assertEquals(Transaction.Status.Authorized, transaction.status);


    def test_retry_charge_with_amount(self):
        subscription = Subscription.search([
            SubscriptionSearch.status.in_list([Subscription.Status.PastDue])
        ]).first

        result = Subscription.retry_charge(subscription.id, Decimal(TransactionAmounts.Authorize));

        self.assertTrue(result.is_success);
        transaction = result.transaction;

        self.assertEquals(Decimal(TransactionAmounts.Authorize), transaction.amount);
        self.assertNotEqual(None, transaction.processor_authorization_code);
        self.assertEquals(Transaction.Type.Sale, transaction.type);
        self.assertEquals(Transaction.Status.Authorized, transaction.status);

