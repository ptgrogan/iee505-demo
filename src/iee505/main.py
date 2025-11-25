from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel, create_engine

from .models import User, UserCreate, UserRead

engine = create_engine(
    "sqlite:///database.db", 
    connect_args={"check_same_thread": False}
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    from .auth import Account, pwd_hash
    with Session(engine) as session:
        try:
            admin=Account(username="admin", hashed_password=pwd_hash.hash("password"))
            session.add(admin)
            session.commit()
        except Exception:
            pass
    yield

app = FastAPI(lifespan=lifespan)

def connect():
    with Session(engine) as session:
        yield session


@app.post("/users")
async def create_user(
    user: UserCreate,
    session: Session = Depends(connect)
) -> int:
    db_user = User.model_validate(user)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user.id


@app.get("/users/{id}")
async def read_user(
    id: int, 
    session: Session = Depends(connect)
) -> UserRead:
    db_user = session.get(User, id)
    if db_user is None:
        raise HTTPException(404, f"User {id} not found")
    return db_user

from sqlmodel import select

@app.get("/users/")
async def read_users(
    session: Session = Depends(connect)
) -> list[UserRead]:
    query = select(User)
    return session.exec(query).all()

@app.put("/users/{id}")
async def update_user(
    id: int,
    user: UserCreate,
    session: Session = Depends(connect)
) -> None:
    db_user = session.get(User, id)
    if db_user is None:
        raise HTTPException(404, f"User {id} not found")
    db_user.sqlmodel_update(user.model_dump())
    session.add(db_user)
    session.commit()

@app.delete("/users/{id}")
async def delete_user(
    id: int,
    session: Session = Depends(connect)
) -> None:
    db_user = session.get(User, id)
    if db_user is None:
        raise HTTPException(404, f"User {id} not found")
    session.delete(db_user)
    session.commit()

from typing import Annotated
from datetime import timedelta
from fastapi import status
from fastapi.security import OAuth2PasswordRequestForm
from .auth import AccountRead, authenticate, create_token, get_current_account, TOKEN_DURATION

class Token(SQLModel):
    access_token: str
    token_type: str

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(connect)
) -> Token:
    account = authenticate(session, form_data.username, form_data.password)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token(
        username=account.username,
        duration=timedelta(minutes=TOKEN_DURATION)
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/accounts/me/")
async def read_accounts_me(
    current_account: Annotated[AccountRead, Depends(get_current_account)],
) -> AccountRead:
    return current_account

from fastapi.staticfiles import StaticFiles

app.mount(
    "/",
    StaticFiles(directory=".", html=True)
)