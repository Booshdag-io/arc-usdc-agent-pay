import hashlib
from src.core.verifier import HashVerifier, CustomCallableVerifier, MinimumThresholdVerifier

def test_hash_verifier_matches_string_and_bytes():
    text = "Machine Learning weights model v2"
    expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
    verifier = HashVerifier(expected_sha256=expected)

    assert verifier.verify(text) is True
    assert verifier.verify(text.encode("utf-8")) is True
    assert verifier.verify({"sha256": expected}) is True
    assert verifier.verify("Wrong content") is False

def test_custom_callable_verifier():
    verifier = CustomCallableVerifier(lambda proof: proof.get("accuracy", 0) > 0.95)
    assert verifier.verify({"accuracy": 0.98}) is True
    assert verifier.verify({"accuracy": 0.85}) is False
    assert verifier.verify("invalid_type") is False

def test_threshold_verifier():
    verifier = MinimumThresholdVerifier(metric_key="fps", min_value=60.0)
    assert verifier.verify({"fps": 120.0}) is True
    assert verifier.verify({"fps": 59.9}) is False
    assert verifier.verify({}) is False
