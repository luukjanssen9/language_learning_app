from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.routes import api_router
from app.config import settings
from app.services.auth import AuthError
from app.services.llm.base import LLMError
from app.services.tts import TTSError

app = FastAPI(title="Language App API", version="0.1.0")

# allow_credentials=True (as of Phase 8 slice 1's Google sign-in) so the
# session cookie actually gets sent/received cross-origin -- still safe
# since allow_origins stays a literal single origin, never a wildcard
# (browsers refuse allow_credentials+wildcard-origin together anyway).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)

app.include_router(api_router, prefix="/api")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Conflicting or invalid reference (duplicate value or bad foreign key)."
        },
    )


@app.exception_handler(LLMError)
async def llm_error_handler(request: Request, exc: LLMError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"LLM provider error: {exc}"},
    )


@app.exception_handler(TTSError)
async def tts_error_handler(request: Request, exc: TTSError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": f"TTS provider error: {exc}"},
    )


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError) -> JSONResponse:
    # `get_current_user` (app/api/auth.py) already catches this locally
    # for a more specific message -- this is the safety net for any other
    # call site (POST /auth/google's own token verification included) that
    # doesn't, so a bad/expired credential 401s cleanly instead of leaking
    # a 500 with a stack trace, found live when a genuinely invalid
    # credential during testing did exactly that.
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
