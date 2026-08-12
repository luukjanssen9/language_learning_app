from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.routes import api_router

app = FastAPI(title="Language App API", version="0.1.0")

app.include_router(api_router, prefix="/api")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": "Conflicting or invalid reference (duplicate value or bad foreign key)."
        },
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
