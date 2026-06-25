from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas import ErrorResponse


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail=ErrorResponse(code=code, message=message).model_dump(),
    )


async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    detail = exc.detail
    if isinstance(detail, dict) and {"success", "code", "message"} <= detail.keys():
        return JSONResponse(status_code=exc.status_code, content=detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code="http_error",
            message=str(detail),
        ).model_dump(),
    )
