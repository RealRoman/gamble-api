from datetime import datetime, timedelta
from typing import Annotated, Union
import random
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import Depends, FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from settings import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, CURSOR, CONNECTION
from pexeso import pexeso_manager
from models import Token, TokenData, User, GuessPexeso, UserCrash
from crash import ws_manager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    user_dict = query_user(username)
    if not user_dict:
        return
    return User(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username already exists",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": form_data.username}, expires_delta=access_token_expires
    )
    create_user(form_data.username, form_data.password)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return current_user

# PEXESO GAME

@app.get("/pexeso/connect/")
async def connect_pexeso_game(
    current_user: Annotated[User, Depends(get_current_user)]
):
    pexeso_manager.new_game(current_user)
    return {'detail': 'success'}

@app.get("/pexeso/disconnect/")
async def disconnect_pexeso_game(
    current_user: Annotated[User, Depends(get_current_user)]
):
    pexeso_manager.disconnect(current_user)
    return {'detail': 'success'}

@app.get("/pexeso/end_game/")
async def end_pexeso_game(
    current_user: Annotated[User, Depends(get_current_user)]
):
    return {'balance': round(pexeso_manager.end_game(current_user), 2)}

@app.post("/pexeso/guess/")
async def make_guess_pexeso_game(
    current_user: Annotated[User, Depends(get_current_user)],
    guess: GuessPexeso
):
    
    return pexeso_manager.guess(user=current_user, x_pos=guess.x_pos, y_pos=guess.y_pos, bet=guess.bet)

# CRASH GAME

@app.websocket("/ws/crash/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    print(username)
    await websocket.accept()
    user = UserCrash(**query_user(username), ws=websocket, bet=0, active=False)
    await ws_manager.connect(user)
    try:
        while True:
            await asyncio.sleep(0.5)
            res = await websocket.receive_json()
            await ws_manager.recieve_message(res, username)
    except WebSocketDisconnect:
        await ws_manager.disconnect(username)

# FUNKCE PRO PRISTUP K DATABAZI

def deconstruct_cursor_one(description: list, resposne: list):
    return {description[i][0]: resposne[i] for i in range(0, len(resposne))}

def query_user(username: str):
    SQL = """
    SELECT id_user, username, password, balance FROM users WHERE username = %s
    """
    CURSOR.execute(SQL, params=[username])
    res = CURSOR.fetchone()
    if not res:
        return False
    return deconstruct_cursor_one(CURSOR.description, res)

def create_user(username: str, password: str):
    hashed_password = get_password_hash(password)
    balance = random.randint(1000, 5000)
    SQL = """
    INSERT INTO users (username, password, balance) VALUES (%s, %s, %s)
    """
    CURSOR.execute(SQL, params=[username, hashed_password, balance])
    CONNECTION.commit()