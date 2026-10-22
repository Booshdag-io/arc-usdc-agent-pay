from decimal import Decimal
from typing import Dict, Optional
from datetime import datetime, timezone
import uuid

class MilestoneEscrow:
    """
    Two-sided milestone escrow allowing agents to contract other agents or humans
    and lock USDC until verifiable acceptance criteria are met.
    """
    def __init__(self, escrow_id: Optional[str] = None):
        self.escrow_id = escrow_id or str(uuid.uuid4())[:8]
        self.tasks: Dict[str, Dict] = {}

    def create_milestone(self, employer_agent: str, worker: str, amount: Decimal, criteria: str) -> str:
        milestone_id = f"ms_{len(self.tasks) + 1}"
        self.tasks[milestone_id] = {
            "id": milestone_id,
            "employer": employer_agent,
            "worker": worker,
            "amount": amount,
            "criteria": criteria,
            "status": "LOCKED",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        return milestone_id

    def release_payment(self, milestone_id: str) -> Dict:
        if milestone_id not in self.tasks:
            raise KeyError(f"Milestone {milestone_id} does not exist.")
        task = self.tasks[milestone_id]
        if task["status"] != "LOCKED":
            raise ValueError(f"Cannot release milestone in status {task['status']}")
        task["status"] = "RELEASED"
        task["settled_at"] = datetime.now(timezone.utc).isoformat()
        return task

    def refund(self, milestone_id: str) -> Dict:
        if milestone_id not in self.tasks:
            raise KeyError(f"Milestone {milestone_id} does not exist.")
        task = self.tasks[milestone_id]
        if task["status"] != "LOCKED":
            raise ValueError(f"Cannot refund milestone in status {task['status']}")
        task["status"] = "REFUNDED"
        task["settled_at"] = datetime.now(timezone.utc).isoformat()
        return task
