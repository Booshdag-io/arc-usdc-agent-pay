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

from src.core.ledger import AuditLedger, TamperedLedgerError

def test_ledger_records_genesis_and_chain():
    ledger = AuditLedger("ledger-test")
    rec1 = ledger.record_event("EVENT_A", {"key": "val1"})
    rec2 = ledger.record_event("EVENT_B", {"key": "val2"})

    assert rec1["index"] == 0
    assert rec1["prev_hash"] == AuditLedger.GENESIS_HASH
    assert rec2["index"] == 1
    assert rec2["prev_hash"] == rec1["hash"]
    assert ledger.verify_integrity() is True

def test_ledger_detects_data_tampering():
    ledger = AuditLedger("ledger-test")
    ledger.record_event("EVENT_A", {"balance": 100})
    ledger.record_event("EVENT_B", {"balance": 50})

    # Tamper with event data in record 0
    ledger.records[0]["data"]["balance"] = 99999

    with pytest.raises(TamperedLedgerError, match="Data tampering detected"):
        ledger.verify_integrity()

def test_ledger_detects_broken_chain_link():
    ledger = AuditLedger("ledger-test")
    ledger.record_event("EVENT_A", {"balance": 100})
    ledger.record_event("EVENT_B", {"balance": 50})

    # Break hash pointer in record 1
    ledger.records[1]["prev_hash"] = "000000000000000000000000000000000000000000000000000000000000dead"

    with pytest.raises(TamperedLedgerError, match="Chain broken"):
        ledger.verify_integrity()
