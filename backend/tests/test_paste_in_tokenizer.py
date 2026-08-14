"""Pure unit tests for the paste-in tokenizer -- no DB, no LLM. Deterministic
and fast enough to call the real `jieba` library directly rather than
faking it.
"""

from app.services.paste_in_tokenizer import tokenize


def _reconstruct(segments: list[tuple[str, bool]]) -> str:
    return "".join(text for text, _ in segments)


def test_whitespace_mode_reconstructs_the_original_text():
    text = "Hola, ¿cómo estás? Tengo 2024 gatos."
    segments = tokenize(text, {})

    assert _reconstruct(segments) == text


def test_whitespace_mode_defaults_when_tokenization_key_absent():
    # Missing "tokenization" key entirely (most languages) behaves the
    # same as an explicit "whitespace" -- default, not an error.
    text = "hola mundo"
    assert tokenize(text, {}) == tokenize(text, {"tokenization": "whitespace"})


def test_whitespace_mode_identifies_word_segments_correctly():
    segments = tokenize("Hola, mundo!", {})
    words = [text for text, is_word in segments if is_word]

    assert words == ["Hola", "mundo"]


def test_whitespace_mode_excludes_purely_numeric_tokens_from_word_hood():
    segments = tokenize("Tengo 2024 gatos.", {})
    words = [text for text, is_word in segments if is_word]

    assert "2024" not in words
    assert words == ["Tengo", "gatos"]


def test_whitespace_mode_handles_accented_letters_as_word_characters():
    segments = tokenize("está aquí", {})
    words = [text for text, is_word in segments if is_word]

    assert words == ["está", "aquí"]


def test_cjk_mode_reconstructs_the_original_text():
    text = "周末，姐姐去了一个大市场。"
    segments = tokenize(text, {"tokenization": "cjk"})

    assert _reconstruct(segments) == text


def test_cjk_mode_identifies_word_segments_and_excludes_punctuation():
    segments = tokenize("周末，姐姐去了一个大市场。", {"tokenization": "cjk"})
    words = [text for text, is_word in segments if is_word]
    punctuation = [text for text, is_word in segments if not is_word]

    assert "周末" in words
    assert "市场" in words
    assert "，" in punctuation
    assert "。" in punctuation
