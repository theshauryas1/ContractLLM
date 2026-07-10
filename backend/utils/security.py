import os
import jwt
import logging
from typing import Optional
from fastapi import Header, Depends, HTTPException
from sqlalchemy.orm import Session
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from backend.utils.config import get_settings
from shared.db.models import get_db, User

logger = logging.getLogger(__name__)

def verify_clerk_token(token: str, public_key: str) -> dict:
    """
    Decodes and verifies a Clerk JWT token using RS256 with the public key.
    """
    # Standardize PEM format
    if "BEGIN PUBLIC KEY" not in public_key:
        # Wrap the key in the standard PEM header/footer if missing
        public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
    
    try:
        # Clerk JWTs are signed with RS256
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except ExpiredSignatureError:
        logger.warning("Authentication failed: Clerk JWT token has expired.")
        raise HTTPException(status_code=401, detail="Token has expired")
    except InvalidTokenError as e:
        logger.warning(f"Authentication failed: Invalid Clerk JWT token: {e}")
        raise HTTPException(status_code=401, detail="Invalid authorization token")

def get_current_user(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency that validates incoming requests via Clerk JWT or legacy API keys.
    Returns the authenticated User model instance, auto-provisioning new users if needed.
    """
    settings = get_settings()

    # 1. Bypass auth if disabled in settings (e.g. testing or local override)
    if not settings.require_auth:
        # Check if we have a default test user or create one
        test_user = db.query(User).filter(User.user_id == "usr_test_default").first()
        if not test_user:
            test_user = User(
                user_id="usr_test_default",
                email="guest@legalaip.com",
                full_name="Guest User",
                preferred_language="en"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        return test_user

    # 2. Check legacy static API key header (x-api-key)
    if x_api_key:
        if x_api_key == settings.api_key:
            api_user = db.query(User).filter(User.user_id == "usr_api_key").first()
            if not api_user:
                api_user = User(
                    user_id="usr_api_key",
                    email="api-key-agent@legalaip.com",
                    full_name="API Key Agent",
                    preferred_language="en"
                )
                db.add(api_user)
                db.commit()
                db.refresh(api_user)
            return api_user
        else:
            raise HTTPException(status_code=401, detail="Invalid API Key")

    # 3. Check Authorization header (Bearer token)
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401, 
            detail="Missing or malformed Authorization header. Expected 'Bearer <token>'"
        )
    
    token = authorization.split(" ")[1]

    # Handle mock tokens in development/testing if no public key is configured
    clerk_pub_key = os.getenv("CLERK_JWT_PUBLIC_KEY")
    if not clerk_pub_key:
        if settings.environment in ("development", "testing"):
            # Decode payload without signature verification in dev/test fallbacks
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub", "usr_dev_fallback")
                email = payload.get("email", f"{user_id}@clerk.user")
                name = payload.get("name", "Clerk Developer")
            except Exception:
                # If token is not a valid JWT but we are in dev/test, treat the token string itself as the user_id
                user_id = f"usr_{token[:12]}"
                email = f"{user_id}@clerk.user"
                name = f"User {user_id}"
                payload = {}
            
            # Sync user to DB
            user = db.query(User).filter(User.user_id == user_id).first()
            if not user:
                user = User(
                    user_id=user_id,
                    email=email,
                    full_name=name,
                    preferred_language=payload.get("lang", "en"),
                    country=payload.get("country"),
                    state=payload.get("state"),
                    timezone=payload.get("tz"),
                )
                db.add(user)
                db.commit()
                db.refresh(user)
            return user
        else:
            logger.error("CLERK_JWT_PUBLIC_KEY is not configured in production environment.")
            raise HTTPException(status_code=500, detail="Server authorization configuration error")

    # 4. Production JWT Verification
    payload = verify_clerk_token(token, clerk_pub_key)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload: missing 'sub'")

    # Extract user profile metadata
    email = payload.get("email") or payload.get("sub") + "@clerk.user"
    name = payload.get("name") or payload.get("full_name") or "Authorized User"
    
    # Sync user details in DB
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            email=email,
            full_name=name,
            preferred_language=payload.get("lang", "en"),
            country=payload.get("country"),
            state=payload.get("state"),
            timezone=payload.get("tz"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user

def require_api_key(
    authorization: Optional[str] = Header(default=None),
    x_api_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
) -> None:
    """
    Backward-compatible dependency that simply asserts the request is authenticated.
    """
    get_current_user(authorization=authorization, x_api_key=x_api_key, db=db)
