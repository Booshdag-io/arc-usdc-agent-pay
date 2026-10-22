from decimal import Decimal
import pytest
from src.core.vault import AgentVault, AgentPolicy, SpendingLimitExceeded

def test_agent_vault_funding():
    vault = AgentVault("agent-001")
    vault.fund(Decimal("100.00"))
    assert vault.balance == Decimal("100.00")

def test_authorized_payment_within_limits():
    vault = AgentVault("agent-001", AgentPolicy(max_single_payment=Decimal("15.00")))
    vault.fund(Decimal("50.00"))
    tx = vault.authorize_and_pay("0xRecipient1", Decimal("5.50"), "Compute payment")
    assert tx["status"] == "COMPLETED"
    assert vault.balance == Decimal("44.50")

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
