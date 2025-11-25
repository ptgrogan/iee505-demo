from sqlmodel import SQLModel, Field, Session
from pwdlib import PasswordHash

class Account(SQLModel, table=True):
    username: str = Field(primary_key=True)
    hashed_password: str

class AccountRead(SQLModel):
    username: str

pwd_hash = PasswordHash.recommended()

def authenticate(
    session: Session,
    username: str,
    password: str
) -> AccountRead:
    account = session.get(Account, username)
    if (
        account is None or 
        not pwd_hash.verify(password, account.hashed_password)
    ):
        return None
    return AccountRead.model_validate(account)

from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = "secret key"
ALGORITHM = "HS256"
TOKEN_DURATION = 30

def create_token(username: str, duration: timedelta | None = None):
    expire = datetime.now(timezone.utc)
    if duration:
        expire += duration
    else:
        expire += timedelta(minutes=TOKEN_DURATION)
    to_encode = {
        "sub": username,
        "exp": expire
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

from typing import Annotated
from fastapi import status, Depends, HTTPException
from jwt.exceptions import InvalidTokenError

async def get_current_account(
    token: Annotated[str, Depends(oauth2_scheme)]
) -> AccountRead:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    return AccountRead(username=username)
