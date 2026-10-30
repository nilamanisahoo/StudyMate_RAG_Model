
from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from slowapi import Limiter
from slowapi.util import get_remote_address

from ..authentication import verify_access_token


# Shared rate limiter for API endpoints.
limiter = Limiter(key_func=get_remote_address)


# Read the Bearer token from the request.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> str:
    """Verify the access token and return the authenticated user's ID."""

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_access_token(credentials.credentials)

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    except RuntimeError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service is not configured correctly.",
        ) from error
