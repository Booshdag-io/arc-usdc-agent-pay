from src.cli.main import main

def test_cli_vault_init(capsys):
    main(["vault-init", "--agent-id", "test-agent", "--initial-fund", "10.00"])
    captured = capsys.readouterr()
    assert "[OK] Agent Vault 'test-agent' initialized successfully!" in captured.out
    assert "10.00 USDC" in captured.out

def test_cli_escrow_demo(capsys):
    main(["escrow-demo", "--amount", "5.00"])
    captured = capsys.readouterr()
    assert "[OK] Milestone created with ID: ms_1" in captured.out

def test_cli_audit_verify(capsys):
    main(["audit-verify"])
    captured = capsys.readouterr()
    assert "[OK] Cryptographic chain intact" in captured.out
    assert "ZERO tampering detected" in captured.out
