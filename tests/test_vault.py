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

from src.core.vault import AgentVault, AgentPolicy, SpendingLimitExceeded, InsufficientVaultFunds

def test_agent_vault_funding():
    vault = AgentVault("agent-001")
    vault.fund(Decimal("100.00"))
    assert vault.balance == Decimal("100.00")

def test_funding_negative_raises_error():
    vault = AgentVault("agent-001")
    with pytest.raises(ValueError):
        vault.fund(Decimal("-5.00"))

def test_authorized_payment_within_limits():
    vault = AgentVault("agent-001", AgentPolicy(max_single_payment=Decimal("15.00")))
    vault.fund(Decimal("50.00"))
    tx = vault.authorize_and_pay("0xRecipient1", Decimal("5.50"), "Compute payment")
    assert tx["status"] == "COMPLETED"
    assert vault.balance == Decimal("44.50")
    assert vault.daily_spent == Decimal("5.50")

def test_payment_exceeding_single_limit_rejected():
    vault = AgentVault("agent-001", AgentPolicy(max_single_payment=Decimal("10.00")))
    vault.fund(Decimal("50.00"))
    with pytest.raises(SpendingLimitExceeded):
        vault.authorize_and_pay("0xRecipient1", Decimal("15.00"), "Too high")

def test_payment_exceeding_daily_limit_rejected():
    vault = AgentVault("agent-001", AgentPolicy(daily_budget_limit=Decimal("20.00"), max_single_payment=Decimal("10.00")))
    vault.fund(Decimal("50.00"))
    vault.authorize_and_pay("0xRecipient1", Decimal("10.00"))
    vault.authorize_and_pay("0xRecipient1", Decimal("10.00"))
    with pytest.raises(SpendingLimitExceeded):
        vault.authorize_and_pay("0xRecipient1", Decimal("5.00"))

def test_payment_exceeding_lifetime_cap():
    vault = AgentVault("agent-001", AgentPolicy(total_lifetime_cap=Decimal("30.00"), daily_budget_limit=Decimal("50.00"), max_single_payment=Decimal("20.00")))
    vault.fund(Decimal("50.00"))
    vault.authorize_and_pay("0xRecipient1", Decimal("20.00"))
    with pytest.raises(SpendingLimitExceeded):
        vault.authorize_and_pay("0xRecipient1", Decimal("15.00"))

def test_insufficient_funds_rejected():
    vault = AgentVault("agent-001")
    vault.fund(Decimal("5.00"))
    with pytest.raises(InsufficientVaultFunds):
        vault.authorize_and_pay("0xRecipient1", Decimal("8.00"))

def test_whitelisted_recipient_enforced():
    vault = AgentVault("agent-001", AgentPolicy(allowed_recipients=["0xAllowed1", "0xAllowed2"]))
    vault.fund(Decimal("50.00"))
    # Allowed
    vault.authorize_and_pay("0xAllowed1", Decimal("5.00"))
    # Not allowed
    with pytest.raises(SpendingLimitExceeded):
        vault.authorize_and_pay("0xRandomStranger", Decimal("5.00"))

def test_vault_telemetry_status():
    vault = AgentVault("agent-telemetry")
    vault.fund(Decimal("25.00"))
    vault.authorize_and_pay("0xRecipient", Decimal("10.00"))
    status = vault.get_status()
    assert status["balance"] == "15.00"
    assert status["daily_spent"] == "10.00"
    assert status["total_transactions"] == 1
