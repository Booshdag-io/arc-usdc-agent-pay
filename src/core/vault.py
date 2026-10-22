from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.core.ledger import AuditLedger

class SpendingLimitExceeded(Exception):
    """Raised when an agent attempts to spend beyond its authorized velocity limits."""
    pass

class InsufficientVaultFunds(Exception):
    """Raised when the vault does not hold enough USDC balance for the operation."""
    pass

class AgentPolicy(BaseModel):
    max_single_payment: Decimal = Field(default=Decimal("10.00"), description="Max USDC allowed per single transaction")
    daily_budget_limit: Decimal = Field(default=Decimal("50.00"), description="Max USDC allowed within a 24-hour cycle")
    total_lifetime_cap: Decimal = Field(default=Decimal("500.00"), description="Max USDC allowed across the lifetime of the vault")
    allowed_recipients: Optional[List[str]] = Field(default=None, description="Optional whitelist of allowed recipient addresses")

class AgentVault:
    """
    Guarded budget vault for autonomous agents to execute micro-payments in USDC safely.
    Enforces velocity limits, whitelists, and logs every movement to an immutable audit ledger.
    """
    def __init__(self, agent_id: str, policy: Optional[AgentPolicy] = None):
        self.agent_id = agent_id
        self.policy = policy or AgentPolicy()
        self.balance: Decimal = Decimal("0.00")
        self.daily_spent: Decimal = Decimal("0.00")
        self.lifetime_spent: Decimal = Decimal("0.00")
        self.last_spend_date = datetime.now(timezone.utc).date()
        self.ledger = AuditLedger(ledger_id=f"vault_{agent_id}")

        # Record initialization in ledger
        self.ledger.record_event("VAULT_INITIALIZED", {
            "agent_id": agent_id,
            "max_single": str(self.policy.max_single_payment),
            "daily_limit": str(self.policy.daily_budget_limit),
            "lifetime_cap": str(self.policy.total_lifetime_cap),
        })

    def _reset_daily_if_new_day(self):
        today = datetime.now(timezone.utc).date()
        if today > self.last_spend_date:
            self.daily_spent = Decimal("0.00")
            self.last_spend_date = today

    def fund(self, amount: Decimal, memo: str = "Vault funding") -> Decimal:
        """Deposit USDC into the agent's operating vault."""
        if amount <= 0:
            raise ValueError("Funding amount must be strictly positive")
        self.balance += amount
        self.ledger.record_event("FUNDS_DEPOSITED", {
            "amount": str(amount),
            "new_balance": str(self.balance),
            "memo": memo,
        })
        return self.balance

    def authorize_and_pay(self, recipient: str, amount: Decimal, memo: str = "") -> Dict[str, Any]:
        """
        Validates the requested payment against all security policies and settles the transfer.
        """
        self._reset_daily_if_new_day()

        if amount <= 0:
            raise ValueError("Payment amount must be strictly greater than zero")

        if self.policy.allowed_recipients is not None and recipient not in self.policy.allowed_recipients:
            raise SpendingLimitExceeded(f"Recipient {recipient} is not on the authorized whitelist.")

        if amount > self.policy.max_single_payment:
            raise SpendingLimitExceeded(
                f"Payment of {amount} USDC exceeds single payment cap of {self.policy.max_single_payment} USDC."
            )

        if (self.daily_spent + amount) > self.policy.daily_budget_limit:
            raise SpendingLimitExceeded(
                f"Payment would exceed daily budget cap of {self.policy.daily_budget_limit} USDC."
            )

        if (self.lifetime_spent + amount) > self.policy.total_lifetime_cap:
            raise SpendingLimitExceeded(
                f"Payment would exceed lifetime cap of {self.policy.total_lifetime_cap} USDC."
            )

        if amount > self.balance:
            raise InsufficientVaultFunds(
                f"Insufficient funds: vault holds {self.balance} USDC, requested {amount} USDC."
            )

        # Deduct funds
        self.balance -= amount
        self.daily_spent += amount
        self.lifetime_spent += amount

        receipt = {
            "tx_id": f"tx_{len(self.ledger.records)}",
            "agent_id": self.agent_id,
            "recipient": recipient,
            "amount": str(amount),
            "remaining_balance": str(self.balance),
            "memo": memo,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED",
        }

        self.ledger.record_event("PAYMENT_EXECUTED", receipt)
        return receipt

    def get_status(self) -> Dict[str, Any]:
        """Returns the current real-time telemetry of the agent vault."""
        self._reset_daily_if_new_day()
        return {
            "agent_id": self.agent_id,
            "balance": str(self.balance),
            "daily_spent": str(self.daily_spent),
            "daily_remaining": str(max(Decimal("0.00"), self.policy.daily_budget_limit - self.daily_spent)),
            "lifetime_spent": str(self.lifetime_spent),
            "lifetime_remaining": str(max(Decimal("0.00"), self.policy.total_lifetime_cap - self.lifetime_spent)),
            "total_transactions": len([r for r in self.ledger.records if r["event_type"] == "PAYMENT_EXECUTED"]),
        }
