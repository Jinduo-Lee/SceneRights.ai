from fastapi import Header, HTTPException, status
from app.config import settings
from app.schemas.enums import ErrorCodeEnum


def raise_api_error(
    status_code: int,
    code: ErrorCodeEnum,
    message: str,
    retryable: bool = False,
    details: dict = None
):
    """Raises a uniform HTTP exception adhering to the Master Spec error envelope."""
    raise HTTPException(
        status_code=status_code,
        detail={
            "error": {
                "code": code.value,
                "message": message,
                "retryable": retryable,
                "details": details or {}
            }
        }
    )


def verify_demo_access_token(
    authorization: str = Header(None, alias="Authorization"),
    x_demo_token: str = Header(None, alias="X-Demo-Token")
):
    """Verifies demo access token from Authorization header or X-Demo-Token header."""
    token = None
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization.split(" ", 1)[1]
        else:
            token = authorization
    elif x_demo_token:
        token = x_demo_token

    if not token or token != settings.DEMO_ACCESS_TOKEN:
        raise_api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ErrorCodeEnum.UNAUTHORIZED,
            message="Invalid or missing demo access token.",
            retryable=False
        )
    return token

