from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.details = details

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "details": exc.details,
            "status_code": exc.status_code,
        },
    ) 