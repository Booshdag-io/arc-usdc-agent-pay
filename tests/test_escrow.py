from decimal import Decimal
import pytest
from src.core.escrow import MilestoneEscrow

def test_milestone_lifecycle():
    escrow = MilestoneEscrow()
    m_id = escrow.create_milestone("agent_A", "agent_B", Decimal("25.00"), "Deliver scraped dataset")
    assert escrow.tasks[m_id]["status"] == "LOCKED"

    res = escrow.release_payment(m_id)
    assert res["status"] == "RELEASED"

def test_milestone_refund():
    escrow = MilestoneEscrow()
    m_id = escrow.create_milestone("agent_A", "agent_B", Decimal("10.00"), "Failed task")
    res = escrow.refund(m_id)
    assert res["status"] == "REFUNDED"
