import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

class TamperedLedgerError(Exception):
    """Raised when ledger integrity verification fails due to data tampering."""
    pass

class AuditLedger:
    """
    Cryptographically chained, tamper-evident audit ledger for autonomous agent transactions.
    Every event references the SHA-256 digest of the preceding record.
    """
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, ledger_id: str):
        self.ledger_id = ledger_id
        self.records: List[Dict[str, Any]] = []

    def _compute_hash(self, prev_hash: str, index: int, timestamp: str, event_type: str, data: Dict[str, Any]) -> str:
        serialized = json.dumps(data, sort_keys=True)
        payload = f"{prev_hash}:{index}:{timestamp}:{event_type}:{serialized}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def record_event(self, event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        index = len(self.records)
        prev_hash = self.records[-1]["hash"] if self.records else self.GENESIS_HASH
        timestamp = datetime.now(timezone.utc).isoformat()
        current_hash = self._compute_hash(prev_hash, index, timestamp, event_type, data)

        record = {
            "index": index,
            "timestamp": timestamp,
            "event_type": event_type,
            "data": data,
            "prev_hash": prev_hash,
            "hash": current_hash,
        }
        self.records.append(record)
        return record

    def verify_integrity(self) -> bool:
        """
        Verifies the cryptographic chain across all recorded events.
        Raises TamperedLedgerError if any record has been modified or corrupted.
        """
        if not self.records:
            return True

        for i, rec in enumerate(self.records):
            expected_prev = self.GENESIS_HASH if i == 0 else self.records[i - 1]["hash"]
            if rec["prev_hash"] != expected_prev:
                raise TamperedLedgerError(
                    f"Chain broken at record #{i}: expected prev_hash {expected_prev}, found {rec['prev_hash']}"
                )

            recomputed = self._compute_hash(
                rec["prev_hash"], rec["index"], rec["timestamp"], rec["event_type"], rec["data"]
            )
            if rec["hash"] != recomputed:
                raise TamperedLedgerError(
                    f"Data tampering detected at record #{i}: recorded hash {rec['hash']}, expected {recomputed}"
                )

        return True

    def export_history(self) -> List[Dict[str, Any]]:
        return list(self.records)
