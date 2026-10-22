from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Optional
from pydantic import BaseModel, Field

class SpendingLimitExceeded(Exception):
    """Raised when an agent tries to spend beyond its authorized limit."""
    pass

class AgentPolicy(BaseModel):
    max_single_payment: Decimal = Field(default=Decimal("10.00"), description="Max USDC per transaction")
    daily_budget_limit: Decimal = Field(default=Decimal("50.00"), description="Max USDC per 24 hours")
    total_lifetime_cap: Decimal = Field(default=Decimal("500.00"), description="Max USDC total")
    allowed_recipients: Optional[list[str]] = Field(default=None, description="Whitelist of recipient addresses")

class AgentVault:
    """
    Guarded budget vault for autonomous agents to execute micro-payments in USDC safely.
    """
    def __init__(self, agent_id: str, policy: Optional[AgentPolicy] = None):
        self.agent_id = agent_id
        self.policy = policy or AgentPolicy()
        self.balance: Decimal = Decimal("0.00")
        self.daily_spent: Decimal = Decimal("0.00")
        self.lifetime_spent: Decimal = Decimal("0.00")
        self.last_spend_date = datetime.now(timezone.utc).date()
        self.transactions: list[Dict] = []

    def fund(self, amount: Decimal) -> Decimal:
        if amount <= 0:
            raise ValueError("Funding amount must be positive")
        self.balance += amount
        return self.balance

    def _reset_daily_if_new_day(self):
        today = datetime.now(timezone.utc).date()
        if today > self.last_spend_date:
            self.daily_spent = Decimal("0.00")
            self.last_spend_date = today

    def authorize_and_pay(self, recipient: str, amount: Decimal, memo: str = "") -> Dict:
        self._reset_daily_if_new_day()

        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero")

        if self.policy.allowed_recipients and recipient not in self.policy.allowed_recipients:
            raise SpendingLimitExceeded(f"Recipient {recipient} is not on the authorized whitelist.")

        if amount > self.policy.max_single_payment:
            raise SpendingLimitExceeded(f"Payment of {amount} USDC exceeds single payment cap of {self.policy.max_single_payment} USDC.")

        if (self.daily_spent + amount) > self.policy.daily_budget_limit:
            raise SpendingLimitExceeded(f"Payment exceeds daily budget cap of {self.policy.daily_budget_limit} USDC.")

        if (self.lifetime_spent + amount) > self.policy.total_lifetime_cap:
            raise SpendingLimitExceeded(f"Payment exceeds lifetime budget cap of {self.policy.total_lifetime_cap} USDC.")

        if amount > self.balance:
            raise ValueError(f"Insufficient funds in agent vault: available {self.balance} USDC, requested {amount} USDC.")

        # Deduct
        self.balance -= amount
        self.daily_spent += amount
        self.lifetime_spent += amount

        tx_record = {
            "tx_id": f"tx_{len(self.transactions) + 1}",
            "agent_id": self.agent_id,
            "recipient": recipient,
            "amount": str(amount),
            "memo": memo,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "COMPLETED"
        }
        self.transactions.append(tx_record)
        return tx_record
