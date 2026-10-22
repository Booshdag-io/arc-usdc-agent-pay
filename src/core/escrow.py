from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
import uuid

from src.core.ledger import AuditLedger
from src.core.verifier import TaskVerifier

class MilestoneEscrow:
    """
    Two-sided milestone escrow allowing agents to contract other agents or humans
    and lock USDC until verifiable acceptance criteria are met.
    Supports automated proof verification and cryptographic auditing.
    """
    def __init__(self, escrow_id: Optional[str] = None):
        self.escrow_id = escrow_id or f"escrow_{str(uuid.uuid4())[:8]}"
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.verifiers: Dict[str, TaskVerifier] = {}
        self.ledger = AuditLedger(ledger_id=self.escrow_id)

    def create_milestone(
        self,
        employer_agent: str,
        worker: str,
        amount: Decimal,
        criteria: str,
        verifier: Optional[TaskVerifier] = None,
    ) -> str:
        """Create a new locked payment milestone with optional automated verification."""
        if amount <= 0:
            raise ValueError("Milestone escrow amount must be strictly positive")

        milestone_id = f"ms_{len(self.tasks) + 1}"
        task = {
            "id": milestone_id,
            "employer": employer_agent,
            "worker": worker,
            "amount": amount,
            "criteria": criteria,
            "status": "LOCKED",
            "has_verifier": verifier is not None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "proof_submitted": None,
            "settled_at": None,
        }
        self.tasks[milestone_id] = task
        if verifier is not None:
            self.verifiers[milestone_id] = verifier

        self.ledger.record_event("MILESTONE_CREATED", {
            "milestone_id": milestone_id,
            "employer": employer_agent,
            "worker": worker,
            "amount": str(amount),
            "criteria": criteria,
        })
        return milestone_id

    def submit_proof_and_verify(self, milestone_id: str, proof: Any) -> Dict[str, Any]:
        """
        Worker submits proof of completion. If a TaskVerifier is registered,
        it evaluates the proof automatically and releases funds upon success.
        """
        if milestone_id not in self.tasks:
            raise KeyError(f"Milestone {milestone_id} does not exist.")

        task = self.tasks[milestone_id]
        if task["status"] != "LOCKED":
            raise ValueError(f"Cannot submit proof for milestone in status {task['status']}")

        task["proof_submitted"] = str(proof)[:200]

        if milestone_id in self.verifiers:
            verifier = self.verifiers[milestone_id]
            is_valid = verifier.verify(proof)
            if is_valid:
                return self.release_payment(milestone_id, reason="Autonomous verification passed")
            else:
                self.ledger.record_event("PROOF_REJECTED", {
                    "milestone_id": milestone_id,
                    "reason": "Proof failed acceptance criteria",
                })
                raise ValueError("Submitted proof failed verification criteria.")
        else:
            self.ledger.record_event("PROOF_SUBMITTED_MANUAL", {
                "milestone_id": milestone_id,
                "note": "Awaiting manual employer release",
            })
            return {"status": "AWAITING_REVIEW", "milestone_id": milestone_id}

    def release_payment(self, milestone_id: str, reason: str = "Work approved") -> Dict[str, Any]:
        """Releases the locked USDC to the worker."""
        if milestone_id not in self.tasks:
            raise KeyError(f"Milestone {milestone_id} does not exist.")

        task = self.tasks[milestone_id]
        if task["status"] != "LOCKED":
            raise ValueError(f"Cannot release milestone in status {task['status']}")

        task["status"] = "RELEASED"
        task["settled_at"] = datetime.now(timezone.utc).isoformat()
        task["resolution_reason"] = reason

        self.ledger.record_event("MILESTONE_RELEASED", {
            "milestone_id": milestone_id,
            "worker": task["worker"],
            "amount": str(task["amount"]),
            "reason": reason,
        })
        return task

    def refund(self, milestone_id: str, reason: str = "Milestone cancelled or expired") -> Dict[str, Any]:
        """Returns the locked USDC back to the employer."""
        if milestone_id not in self.tasks:
            raise KeyError(f"Milestone {milestone_id} does not exist.")

        task = self.tasks[milestone_id]
        if task["status"] != "LOCKED":
            raise ValueError(f"Cannot refund milestone in status {task['status']}")

        task["status"] = "REFUNDED"
        task["settled_at"] = datetime.now(timezone.utc).isoformat()
        task["resolution_reason"] = reason

        self.ledger.record_event("MILESTONE_REFUNDED", {
            "milestone_id": milestone_id,
            "employer": task["employer"],
            "amount": str(task["amount"]),
            "reason": reason,
        })
        return task
