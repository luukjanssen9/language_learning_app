from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.routes import api_router
from app.config import settings
from app.services.llm.base import LLMError
from app.services.tts import TTSError

app = FastAPI(title="Language App API", version="0.1.0")

# No auth/cookies in v1, so allow_credentials stays False -- the frontend
# never sends credentialed requests, keeping this the simple case of CORS
# (a literal origin allow-list, no wildcard-with-credentials footgun).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=False,
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


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
