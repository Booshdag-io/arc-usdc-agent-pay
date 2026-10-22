from decimal import Decimal
from typing import Any, Dict, Optional
import os
import uuid

class CircleWalletClient:
    """
    Adapter for Circle's Programmable Wallets API (Developer-Controlled Wallets).
    Allows autonomous agents to manage programmatic USDC balances on Arc and EVM chains.
    Operates in MOCK mode for unit tests and local simulations when no CIRCLE_API_KEY is provided.
    """
    BASE_URL = "https://api.circle.com/v1/w3s"

    def __init__(self, api_key: Optional[str] = None, entity_secret: Optional[str] = None, sandbox: bool = True):
        self.api_key = api_key or os.getenv("CIRCLE_API_KEY")
        self.entity_secret = entity_secret or os.getenv("CIRCLE_ENTITY_SECRET")
        self.sandbox = sandbox
        self.is_mock = not bool(self.api_key)

        # In-memory ledger for mock simulation
        self._mock_wallets: Dict[str, Dict[str, Any]] = {}

    def create_developer_wallet(self, description: str = "Agent Vault Wallet") -> Dict[str, Any]:
        """Provisions a developer-controlled Circle wallet for an autonomous agent."""
        if self.is_mock:
            wallet_id = f"wallet_{str(uuid.uuid4())[:12]}"
            address = f"0x{uuid.uuid4().hex[:40]}"
            wallet = {
                "wallet_id": wallet_id,
                "address": address,
                "blockchain": "ARC-TESTNET" if self.sandbox else "ARC-MAINNET",
                "description": description,
                "usdc_balance": Decimal("0.00"),
                "status": "ACTIVE",
            }
            self._mock_wallets[wallet_id] = wallet
            return wallet

        # Real Circle API request would be sent here
        raise NotImplementedError("Live Circle API call requires valid CIRCLE_API_KEY credentials.")

    def get_usdc_balance(self, wallet_id: str) -> Decimal:
        """Retrieves the real-time USDC balance for the specified wallet ID."""
        if self.is_mock:
            if wallet_id not in self._mock_wallets:
                raise KeyError(f"Wallet {wallet_id} not found in mock store.")
            return self._mock_wallets[wallet_id]["usdc_balance"]

        raise NotImplementedError("Live Circle API call requires valid CIRCLE_API_KEY credentials.")

    def mock_deposit(self, wallet_id: str, amount: Decimal) -> Decimal:
        """Helper for test simulations: deposit testnet USDC into a mock wallet."""
        if not self.is_mock:
            raise RuntimeError("mock_deposit is only permitted in mock/simulation mode.")
        if wallet_id not in self._mock_wallets:
            raise KeyError(f"Wallet {wallet_id} not found.")
        self._mock_wallets[wallet_id]["usdc_balance"] += amount
        return self._mock_wallets[wallet_id]["usdc_balance"]

    def transfer_usdc(
        self,
        wallet_id: str,
        destination_address: str,
        amount: Decimal,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a programmatic USDC transfer from an agent's Circle wallet to a recipient.
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be strictly positive")

        if self.is_mock:
            if wallet_id not in self._mock_wallets:
                raise KeyError(f"Wallet {wallet_id} not found.")

            wallet = self._mock_wallets[wallet_id]
            if wallet["usdc_balance"] < amount:
                raise ValueError(
                    f"Insufficient funds: available {wallet['usdc_balance']} USDC, requested {amount} USDC"
                )

            wallet["usdc_balance"] -= amount
            tx_id = f"circle_tx_{str(uuid.uuid4())[:16]}"
            return {
                "transaction_id": tx_id,
                "wallet_id": wallet_id,
                "destination_address": destination_address,
                "amount": str(amount),
                "token": "USDC",
                "idempotency_key": idempotency_key or str(uuid.uuid4()),
                "status": "CONFIRMED",
            }

        raise NotImplementedError("Live Circle API call requires valid CIRCLE_API_KEY credentials.")
