"""Splits arbitrary pasted text into segments for unknown-word flagging.
Pure function, no DB access -- same convention as this project's other
services; the caller (route) checks each word segment against the known-
word set.

Reconstructive by construction: joining the returned segments' text in
order always reproduces the input exactly, so the frontend can render
highlights without re-deriving anything from the original string.

Branches on `grammar_config.get("tokenization", "whitespace")` -- a config
value, not a language identity check, matching this project's existing
`script_direction`/`vocab_deck` convention. "whitespace" (the default:
Spanish, Dutch) splits on Unicode word-character runs directly; "cjk"
(Chinese) uses real word segmentation via `jieba`, since CJK text has no
spaces between words -- naive splitting would flag individual characters
instead of words.
"""

import re

import jieba

# Unicode "word" characters minus digits/underscore -- letters only
# (Python's \w is already Unicode-aware, so this covers accented Spanish/
# Dutch letters for free). Purely numeric runs ("2024") are excluded from
# word-hood by construction, not a separate filter step.
_WHITESPACE_WORD_PATTERN = re.compile(r"([^\W\d_]+)")

_CJK_IDEOGRAPH_PATTERN = re.compile(r"[一-鿿]")


def _tokenize_whitespace(text: str) -> list[tuple[str, bool]]:
    parts = _WHITESPACE_WORD_PATTERN.split(text)
    # re.split with a capturing group interleaves separators and matched
    # groups, starting and ending with a (possibly empty) separator --
    # odd indices are always the captured words.
    return [(part, i % 2 == 1) for i, part in enumerate(parts) if part]


def _tokenize_cjk(text: str) -> list[tuple[str, bool]]:
    segments: list[tuple[str, bool]] = []
    for word, _start, _end in jieba.tokenize(text):
        segments.append((word, bool(_CJK_IDEOGRAPH_PATTERN.search(word))))
    return segments


def tokenize(text: str, grammar_config: dict) -> list[tuple[str, bool]]:
    mode = grammar_config.get("tokenization", "whitespace")
    if mode == "cjk":
        return _tokenize_cjk(text)
    return _tokenize_whitespace(text)
