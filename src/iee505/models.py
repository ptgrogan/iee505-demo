from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: int | None = Field(
        default=None, 
        primary_key=True
    )
    name: str

class UserCreate(SQLModel):
    name: str

class UserRead(SQLModel):
    id: int
    name: str