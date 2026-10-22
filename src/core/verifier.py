import abc
import hashlib
from typing import Any, Callable, Dict, Optional

class TaskVerifier(abc.ABC):
    """Abstract Base Class for autonomous task completion verifiers."""

    @abc.abstractmethod
    def verify(self, proof: Any) -> bool:
        """Evaluate whether the submitted proof satisfies the acceptance criteria."""
        pass

class HashVerifier(TaskVerifier):
    """
    Verifies that the SHA-256 digest of delivered data matches the expected commitment.
    Used for dataset deliveries, compute artifacts, or code blobs.
    """
    def __init__(self, expected_sha256: str):
        self.expected_sha256 = expected_sha256.lower()

    def verify(self, proof: Any) -> bool:
        if isinstance(proof, bytes):
            digest = hashlib.sha256(proof).hexdigest().lower()
        elif isinstance(proof, str):
            digest = hashlib.sha256(proof.encode("utf-8")).hexdigest().lower()
        elif isinstance(proof, dict) and "sha256" in proof:
            digest = str(proof["sha256"]).lower()
        else:
            return False
        return digest == self.expected_sha256

class CustomCallableVerifier(TaskVerifier):
    """Verifies acceptance criteria using a programmatic Python callback."""
    def __init__(self, predicate: Callable[[Any], bool]):
        self.predicate = predicate

    def verify(self, proof: Any) -> bool:
        try:
            return bool(self.predicate(proof))
        except Exception:
            return False

class MinimumThresholdVerifier(TaskVerifier):
    """Verifies that a numeric metric reported in the proof meets or exceeds a target value."""
    def __init__(self, metric_key: str, min_value: float):
        self.metric_key = metric_key
        self.min_value = min_value

    def verify(self, proof: Any) -> bool:
        if not isinstance(proof, dict):
            return False
        value = proof.get(self.metric_key)
        if value is None:
            return False
        try:
            return float(value) >= self.min_value
        except (ValueError, TypeError):
            return False
