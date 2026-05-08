"""Payment processing - contains intentional security and complexity issues."""


class PaymentProcessor:
    STRIPE_KEY = "sk_live_ABCDEFGH12345678"  # ISSUE: Hardcoded API key

    def charge(self, amount: float, card_token: str):
        # ISSUE: No error handling for invalid input
        result = amount * 1.029 + 0.30  # processing fee
        return {"status": "charged", "amount": result}

    def refund(self, transaction_id: str):
        try:
            # Process refund
            pass
        except:
            # ISSUE: Bare except
            return None

    def calculate_tax(self, amount, rate, discount, coupon, gift_card, loyalty_points):
        # ISSUE: Too many parameters
        pass

    def process_batch(self, payments):
        """Process multiple payments."""
        for payment in payments:
            if payment.get("type") == "credit":
                if payment.get("amount", 0) > 100:
                    if payment.get("currency") == "USD":
                        # ISSUE: Deeply nested
                        if payment.get("verified"):
                            self.charge(payment["amount"], payment.get("token"))


# TODO: Add PayPal integration
# FIXME: Currency conversion broken
# HACK: Skip CVV verification in test mode
