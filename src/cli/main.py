import argparse
from decimal import Decimal
import sys
from typing import List, Optional

from src.core.vault import AgentVault, AgentPolicy
from src.core.escrow import MilestoneEscrow
from src.core.verifier import HashVerifier
from src.core.ledger import TamperedLedgerError

def format_banner():
    return """
========================================================================
⚡ Arc USDC Agent Pay CLI - Autonomous Micro-Payment & Escrow Engine
Built for Circle USDC & Arc | Developed by Booshdag
========================================================================
"""

def handle_vault_init(args):
    policy = AgentPolicy(
        max_single_payment=Decimal(args.max_single),
        daily_budget_limit=Decimal(args.daily_limit),
        total_lifetime_cap=Decimal(args.lifetime_cap),
    )
    vault = AgentVault(agent_id=args.agent_id, policy=policy)
    vault.fund(Decimal(args.initial_fund))
    status = vault.get_status()
    print(f"[OK] Agent Vault '{args.agent_id}' initialized successfully!")
    print(f"     Balance:          {status['balance']} USDC")
    print(f"     Max Single Cap:   {args.max_single} USDC")
    print(f"     Daily Budget:     {status['daily_remaining']} USDC remaining")
    print(f"     Lifetime Cap:     {args.lifetime_cap} USDC")

def handle_escrow_demo(args):
    print(f"[+] Creating Milestone Escrow between {args.employer} and {args.worker}...")
    escrow = MilestoneEscrow()
    verifier = HashVerifier(expected_sha256=args.expected_hash)
    m_id = escrow.create_milestone(
        employer_agent=args.employer,
        worker=args.worker,
        amount=Decimal(args.amount),
        criteria=args.criteria,
        verifier=verifier,
    )
    print(f"[OK] Milestone created with ID: {m_id} (Status: LOCKED)")
    print(f"     Locked Funds:     {args.amount} USDC")
    print(f"     Criteria:         {args.criteria}")
    print(f"     Expected SHA-256: {args.expected_hash}")
    return m_id

def handle_audit_verify(args):
    print("[+] Auditing transaction ledger integrity...")
    vault = AgentVault(agent_id="audit_demo")
    vault.fund(Decimal("100.00"))
    vault.authorize_and_pay("0xWorker1", Decimal("5.00"), "Task compute")
    vault.authorize_and_pay("0xWorker2", Decimal("10.00"), "Dataset query")
    try:
        vault.ledger.verify_integrity()
        print(f"[OK] Cryptographic chain intact across {len(vault.ledger.records)} ledger blocks. ZERO tampering detected.")
    except TamperedLedgerError as e:
        print(f"[FAIL] Ledger tampering detected: {e}")
        sys.exit(1)

def main(cli_args: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="Arc USDC Agent Pay - Guarded micro-payments and escrow for AI agents",
    )
    subparsers = parser.add_subparsers(dest="command")

    # vault init
    p_vault = subparsers.add_parser("vault-init", help="Initialize a guarded agent vault")
    p_vault.add_argument("--agent-id", default="agent-001", help="Unique identifier of agent")
    p_vault.add_argument("--max-single", default="10.00", help="Max USDC per transaction")
    p_vault.add_argument("--daily-limit", default="50.00", help="Max USDC per 24 hours")
    p_vault.add_argument("--lifetime-cap", default="500.00", help="Max USDC total")
    p_vault.add_argument("--initial-fund", default="25.00", help="Initial USDC deposit")

    # escrow demo
    p_escrow = subparsers.add_parser("escrow-demo", help="Create milestone escrow with hash verification")
    p_escrow.add_argument("--employer", default="ai-coordinator-1")
    p_escrow.add_argument("--worker", default="ai-worker-42")
    p_escrow.add_argument("--amount", default="15.00")
    p_escrow.add_argument("--criteria", default="Deliver clean JSON dataset")
    p_escrow.add_argument("--expected-hash", default="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

    # audit verify
    p_audit = subparsers.add_parser("audit-verify", help="Run cryptographic verification on the audit chain")

    args = parser.parse_args(cli_args)

    if args.command == "vault-init":
        handle_vault_init(args)
    elif args.command == "escrow-demo":
        handle_escrow_demo(args)
    elif args.command == "audit-verify":
        handle_audit_verify(args)
    else:
        print(format_banner())
        parser.print_help()

if __name__ == "__main__":
    main()
