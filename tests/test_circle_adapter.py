from decimal import Decimal
try:
    import pytest
except ImportError:
    class _RaisesContext:
        def __init__(self, expected, match=None):
            self.expected = expected
            self.match = match
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is None:
                raise AssertionError(f'Expected {self.expected.__name__} was not raised.')
            if not issubclass(exc_type, self.expected):
                return False
            if self.match and self.match not in str(exc_val):
                raise AssertionError(f'Pattern {self.match} not found in {exc_val}')
            return True

    class _MockPytest:
        @staticmethod
        def raises(expected, match=None):
            return _RaisesContext(expected, match)
    pytest = _MockPytest()

from src.adapters.circle import CircleWalletClient

def test_circle_mock_wallet_creation_and_deposit():
    client = CircleWalletClient(sandbox=True)
    assert client.is_mock is True

    wallet = client.create_developer_wallet(description="Test Agent Wallet")
    assert wallet["wallet_id"].startswith("wallet_")
    assert wallet["address"].startswith("0x")
    assert wallet["usdc_balance"] == Decimal("0.00")

    # Mock deposit
    new_bal = client.mock_deposit(wallet["wallet_id"], Decimal("150.00"))
    assert new_bal == Decimal("150.00")
    assert client.get_usdc_balance(wallet["wallet_id"]) == Decimal("150.00")

def test_circle_mock_transfer_success():
    client = CircleWalletClient(sandbox=True)
    wallet = client.create_developer_wallet()
    client.mock_deposit(wallet["wallet_id"], Decimal("50.00"))

    res = client.transfer_usdc(
        wallet_id=wallet["wallet_id"],
        destination_address="0xRecipient999",
        amount=Decimal("20.00"),
    )
    assert res["status"] == "CONFIRMED"
    assert res["amount"] == "20.00"
    assert client.get_usdc_balance(wallet["wallet_id"]) == Decimal("30.00")

def test_circle_mock_transfer_insufficient_funds():
    client = CircleWalletClient(sandbox=True)
    wallet = client.create_developer_wallet()
    client.mock_deposit(wallet["wallet_id"], Decimal("10.00"))

    with pytest.raises(ValueError, match="Insufficient funds"):
        client.transfer_usdc(
            wallet_id=wallet["wallet_id"],
            destination_address="0xRecipient999",
            amount=Decimal("50.00"),
        )
