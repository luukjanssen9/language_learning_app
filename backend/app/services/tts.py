"""Wraps Google Cloud Text-to-Speech. The only module that imports
`google.cloud.texttospeech` directly -- same "one module owns the
third-party library" convention as `fsrs_engine.py`/`llm/gemini.py`.

Not built as a swappable-provider abstraction the way `LLMProvider` is:
only one TTS provider is in scope, and this project's own precedent
(Dutch's participle-formation fallback, the vocab-deck framework) is to
not build pluggability until a second real user of it exists -- see
PLAN.md's 2026-08-14 "TTS audio for vocab cards" decision.
"""

from google.cloud import texttospeech


class TTSError(Exception):
    """Raised on a Google Cloud TTS request failure. Callers (routes) are
    expected to let this propagate -- `app/main.py` maps it to a 502,
    the same way `LLMError`/`IntegrityError` are mapped globally.
    """


_client: texttospeech.TextToSpeechAsyncClient | None = None


async def get_tts_client() -> texttospeech.TextToSpeechAsyncClient:
    """Credentials come from `GOOGLE_APPLICATION_CREDENTIALS` (see
    docker-compose.yml), auto-discovered by the client library itself
    (Application Default Credentials) -- not a `Settings` field, since
    that env var is the standard, library-native way this is meant to
    be configured. Exposed as a FastAPI dependency so tests can override
    it with a fake, same mechanism as `get_db`/`get_llm_provider`.

    Deliberately `async def` with a manual module-level singleton,
    unlike `get_llm_provider`/`get_settings`'s `@lru_cache` on a sync
    function: FastAPI runs sync dependencies in a worker thread pool,
    but `TextToSpeechAsyncClient`'s grpc.aio transport binds to the
    event loop of the thread it's constructed on, and anyio worker
    threads don't have one -- constructing it there raises "There is no
    current event loop in thread". An async dependency is awaited
    directly on the real event loop instead, avoiding the issue.
    """
    global _client
    if _client is None:
        _client = texttospeech.TextToSpeechAsyncClient()
    return _client


async def synthesize_speech(
    client: texttospeech.TextToSpeechAsyncClient,
    text: str,
    language_code: str,
    voice_name: str,
) -> bytes:
    """Returns MP3-encoded audio bytes for `text`, spoken in the given
    voice. `language_code`/`voice_name` come from a target `Language`'s
    `grammar_config.tts` -- per-language data, never hardcoded here.
    """
    try:
        response = await client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=texttospeech.VoiceSelectionParams(
                language_code=language_code, name=voice_name
            ),
            audio_config=texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            ),
        )
    except Exception as exc:
        raise TTSError(f"Google Cloud TTS request failed: {exc}") from exc
    return response.audio_content
