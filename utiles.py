from datetime import datetime, timedelta, timezone
from functools import wraps
from jwt.exceptions  import InvalidTokenError 
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from database import *
from schemas import TokenData, UserResponse
from passlib.context import CryptContext
from models import User
from typing import Annotated
from jose import jwt
import jwt
import http

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Schéma OAuth2 pour l'authentification
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configure passlib pour utiliser bcrypt pour le hachage des mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db : Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        role: str = payload.get("role")
        if user_id is None or role is None:
            raise credentials_exception
        token_data = TokenData(user_id=str(user_id), role=role)
    except InvalidTokenError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id==int(token_data.user_id)).first()
    if user is None:
        raise credentials_exception
    return user

def role_required(roles):
    """
    Vérifie si l'utilisateur a un des rôles requis.
    Si 'roles' est une chaîne, elle est convertie en liste contenant un seul élément.
    """
    # Assurer que roles est une liste
    if isinstance(roles, str):
        roles = [roles]
        
    def role_verification(current_user: UserResponse = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé : Vous devez avoir l'un des rôles suivants {roles} pour accéder à cette ressource."
            )
        return current_user
    
    return role_verification


def handle_db_error(func):
    """
    Décorateur pour gérer les erreurs de base de données.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except SQLAlchemyError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erreur de base de données: {str(e)}"
            )
    return wrapper