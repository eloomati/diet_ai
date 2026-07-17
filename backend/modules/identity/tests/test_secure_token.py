from backend.modules.identity.domain.services.secure_token import SecureToken


def test_generate_returns_raw_and_hash() -> None:
    raw_token, token_hash = SecureToken.generate()

    assert isinstance(raw_token, str) and len(raw_token) > 20
    assert token_hash != raw_token
    assert token_hash == SecureToken.hash(raw_token)


def test_generate_produces_distinct_tokens_each_call() -> None:
    raw_a, hash_a = SecureToken.generate()
    raw_b, hash_b = SecureToken.generate()

    assert raw_a != raw_b
    assert hash_a != hash_b


def test_hash_is_deterministic() -> None:
    assert SecureToken.hash("same-input") == SecureToken.hash("same-input")


def test_hash_differs_for_different_input() -> None:
    assert SecureToken.hash("a") != SecureToken.hash("b")
