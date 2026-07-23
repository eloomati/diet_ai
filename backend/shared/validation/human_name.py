import re

# Letters (ASCII + Polish diacritics) and digits, in "words" separated by
# exactly one space — no leading/trailing space, no double spaces, no other
# special characters. Digits are allowed deliberately: this same rule backs
# both a free-choice display name/nickname (where "Jan99" is fine) and a
# dietitian's real first/last name, per the project's own decision to
# share one rule rather than have two.
_WORD = r"[A-Za-z0-9ĄĆĘŁŃÓŚŹŻąćęłńóśźż]+"
_HUMAN_NAME_RE = re.compile(rf"^{_WORD}( {_WORD})*$")
MAX_HUMAN_NAME_LENGTH = 50

# Pure, dependency-free — no module's domain exception is raised here, so
# this can live in the Shared Kernel without creating a shared-depends-on-
# module dependency (see docs/architecture.md's Shared Kernel section).
# Each module's own value object / entity calls this and raises its own
# domain exception on failure.


def is_valid_human_name(value: str) -> bool:
    return bool(value) and len(value) <= MAX_HUMAN_NAME_LENGTH and bool(_HUMAN_NAME_RE.match(value))
