from typing import  Union, Any
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    id_user: int
    username: Union[str, None] = None
    password: Union[str, None] = None
    balance: Union[int, None] = None

class UserCrash(User):
    ws: Any
    bet: int
    active: bool

    
class GuessPexeso(BaseModel):
    x_pos: int = Field(None, ge=0, le=4)
    y_pos: int = Field(None, ge=0, le=4)
    bet: int
