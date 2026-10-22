"""
End-to-end Autonomous Agent Micro-Payment & Escrow Workflow.
Demonstrates:
  1. Setting up an Agent Vault with velocity limits.
  2. Locking funds in Milestone Escrow for a task.
  3. Worker autonomous proof-of-work submission.
  4. Automatic cryptographic verification and instant USDC settlement.
  5. Immutable audit ledger verification.
"""

from decimal import Decimal
import hashlib
import json
from src.core.vault import AgentVault, AgentPolicy
from src.core.escrow import MilestoneEscrow
from src.core.verifier import HashVerifier

def run_agent_workflow():
    print("=" * 70)
    print("🤖 STARTING AUTONOMOUS AGENT WORKFLOW WITH CIRCLE USDC ESCROW")
    print("=" * 70)

    # 1. Employer Agent initializes guarded vault
    employer_vault = AgentVault(
        agent_id="agent-coordinator-alpha",
        policy=AgentPolicy(
            max_single_payment=Decimal("20.00"),
            daily_budget_limit=Decimal("100.00"),
            total_lifetime_cap=Decimal("1000.00")
        )
    )
    employer_vault.fund(Decimal("50.00"), memo="Initial seed deposit")
    print(f"\n[1] Employer Agent initialized. Balance: {employer_vault.balance} USDC")

    # 2. Worker produces a computation artifact
    worker_artifact = json.dumps({"status": "SUCCESS", "records_indexed": 15000, "checksum": "abc99"}).encode("utf-8")
    expected_digest = hashlib.sha256(worker_artifact).hexdigest()
    print(f"[2] Expected artifact hash commitment: {expected_digest}")

    # 3. Create Milestone Escrow with HashVerifier
    escrow = MilestoneEscrow(escrow_id="escrow_job_42")
    verifier = HashVerifier(expected_sha256=expected_digest)

    milestone_id = escrow.create_milestone(
        employer_agent="agent-coordinator-alpha",
        worker="0xWorkerComputeAddress789",
        amount=Decimal("12.50"),
        criteria="Index 15,000 market order records",
        verifier=verifier
    )
    print(f"[3] Escrow milestone created: {milestone_id} | Locked: 12.50 USDC")

    # 4. Worker submits completed work artifact
    print("\n[4] Worker submitting work proof to escrow engine...")
    resolution = escrow.submit_proof_and_verify(milestone_id, proof=worker_artifact)
    print(f"    Status: {resolution['status']}")
    print(f"    Settled at: {resolution['settled_at']}")
    print(f"    Resolution Reason: {resolution['resolution_reason']}")

    # 5. Verify Audit Ledger integrity
    print("\n[5] Auditing cryptographic transaction chain...")
    escrow.ledger.verify_integrity()
    print(f"    Audit chain: {len(escrow.ledger.records)} records verified with ZERO tampering.")

    print("\n" + "=" * 70)
    print("✅ WORKFLOW COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_agent_workflow()
