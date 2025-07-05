from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from privy import PrivyAPI
from app.config import config
import jwt

# Set up OAuth2PasswordBearer for OpenAPI and dependency injection
# The tokenUrl is a dummy, since we only verify tokens, not issue them
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Privy client setup (app_id and app_secret should be in config)
if config.env.endswith("dev") or config.env.endswith("prod"):
    privy_client = PrivyAPI(app_id=config.privy_app_id, app_secret=config.privy_api_key)


async def get_user_id(token: str = Depends(oauth2_scheme)) -> str:
    """Validate the Privy access token and return the user's Privy DID (user_id)."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
        )
    try:
        if config.env.endswith("dev") or config.env.endswith("prod"):
            user = privy_client.users.verify_access_token(auth_token=token)
            # user is an AccessTokenClaims object, user.user_id is the DID
            privy_client.users.get(user_id=user["user_id"])
            return user["user_id"]
        elif config.jwt_secret:
            payload = jwt.decode(token, config.jwt_secret, algorithms=["HS256"])
            return payload["sub"]
        else:
            return "test_user_id"
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
