import pytest

from backend.shared.validation import MAX_HUMAN_NAME_LENGTH, is_valid_human_name


@pytest.mark.parametrize(
    "value",
    [
        "Jan",
        "Jan Kowalski",
        "Ola Ćwik",
        "Żaneta",
        "Jan99",
        "A",
        "a" * MAX_HUMAN_NAME_LENGTH,
    ],
)
def test_accepts_letters_digits_and_single_spaces(value: str) -> None:
    assert is_valid_human_name(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "Jan  Kowalski",  # double space
        " Jan",  # leading space
        "Jan ",  # trailing space
        "Jan-Kowalski",  # hyphen
        "Jan_Kowalski",  # underscore
        "Jan.Kowalski",  # period
        "Jan@Kowalski",
        "'; DROP TABLE users; --",
        "<script>alert(1)</script>",
        "a" * (MAX_HUMAN_NAME_LENGTH + 1),
    ],
)
def test_rejects_special_characters_bad_spacing_and_overlength(value: str) -> None:
    assert is_valid_human_name(value) is False
