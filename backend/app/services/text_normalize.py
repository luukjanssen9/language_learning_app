"""Accent- and case-insensitive text comparison, shared by anything that
needs to treat "adios" and "Adiós" as the same string -- originally
`exercise_grading.py`'s private `_normalize` (2026-08-14, "typing Spanish
accents on a US keyboard is real friction"), extracted here once
`cards.py`'s quick-add dedup became a second real caller.
"""

import unicodedata


def normalize_for_comparison(text: str) -> str:
    # NFKD decomposes an accented character into base + combining mark
    # (e.g. "á" -> "a" + U+0301); dropping the marks (Unicode category
    # "Mn") leaves the unaccented base letters.
    decomposed = unicodedata.normalize("NFKD", text.strip().lower())
    return "".join(c for c in decomposed if not unicodedata.combining(c))
