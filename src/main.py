# ai-generated: 80% - FastAPI shell created from the course requirements and HTTP contract; no ticket logic yet
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI(title="svcdesk", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": f"{request.url.path} not found"}},
        )
    if exc.status_code == 405:
        return JSONResponse(
            status_code=405,
            content={"error": {"code": "method_not_allowed", "message": "method not allowed"}},
        )
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "http_error", "message": exc.detail}})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation", "message": "invalid request body"}},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=False)
