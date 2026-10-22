from decimal import Decimal
import hashlib
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

from src.core.escrow import MilestoneEscrow
from src.core.verifier import HashVerifier

def test_milestone_manual_lifecycle():
    escrow = MilestoneEscrow()
    m_id = escrow.create_milestone("agent_A", "agent_B", Decimal("25.00"), "Deliver scraped dataset")
    assert escrow.tasks[m_id]["status"] == "LOCKED"

    res = escrow.release_payment(m_id)
    assert res["status"] == "RELEASED"
    assert res["settled_at"] is not None

def test_milestone_refund():
    escrow = MilestoneEscrow()
    m_id = escrow.create_milestone("agent_A", "agent_B", Decimal("10.00"), "Failed task")
    res = escrow.refund(m_id)
    assert res["status"] == "REFUNDED"

def test_milestone_autonomous_hash_verification():
    raw_data = b"Clean tabular dataset v1.0"
    digest = hashlib.sha256(raw_data).hexdigest()

    escrow = MilestoneEscrow()
    verifier = HashVerifier(expected_sha256=digest)
    m_id = escrow.create_milestone("agent_A", "worker_X", Decimal("15.00"), "Deliver data", verifier=verifier)

    # Worker submits matching proof
    res = escrow.submit_proof_and_verify(m_id, proof=raw_data)
    assert res["status"] == "RELEASED"
    assert "Autonomous verification passed" in res["resolution_reason"]

def test_milestone_invalid_proof_rejected():
    escrow = MilestoneEscrow()
    verifier = HashVerifier(expected_sha256="ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff")
    m_id = escrow.create_milestone("agent_A", "worker_X", Decimal("15.00"), "Deliver data", verifier=verifier)

    with pytest.raises(ValueError, match="failed verification criteria"):
        escrow.submit_proof_and_verify(m_id, proof=b"Tampered bad data")

    # Milestone remains locked after failed proof
    assert escrow.tasks[m_id]["status"] == "LOCKED"

def test_cannot_release_twice():
    escrow = MilestoneEscrow()
    m_id = escrow.create_milestone("agent_A", "agent_B", Decimal("5.00"), "Task")
    escrow.release_payment(m_id)
    with pytest.raises(ValueError):
        escrow.release_payment(m_id)
