from fastapi import APIRouter, Depends, Request, HTTPException
from database import get_db, Base
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from .auth import User, EmailStr
from utils.utils import decode_token, hash_password

users_router = APIRouter()


class UserCreate(BaseModel): # validation
      username: str = Field(min_length=6, max_length=20)
      email: str = EmailStr
      password: str = Field(min_length=8, max_length=16)
      money: float = Field(ge=0, default=0)
      model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=6, max_length=20)
    password: str | None = Field(default=None, min_length=8, max_length=16)
    money: float  | None = Field(default=None, ge=0)

def require_admin(request: Request, db: Session):
    authorization = request.headers.get("authorization", "")
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    payload = decode_token(authorization.split(" ", 1)[1])
    if not payload or not payload.get("sub"):
        raise HTTPException(401, "Invalid or expired token")
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user or user.role.value != "admin":
        raise HTTPException(403, "Admin access required")
    return user


@users_router.post("/users")
def create_user(user: UserCreate, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    new_user = User(username=user.username, email=user.email, password=hash_password(user.password), money=user.money)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@users_router.get("/users/{id}")
def get_user(id, db:Session = Depends(get_db)):
   user = db.query(User).filter(User.id == id).first()
   return user

@users_router.get("/users")
def get_users(request: Request, db:Session = Depends(get_db)):
   require_admin(request, db)
   user = db.query(User).all()
   return user

@users_router.put("/users")
def update_users(id: str, user_data: UserUpdate, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    user = db.query(User).filter(User.id == id).first()  
    if not user:
        raise HTTPException(404, "User not found")

    if user_data.username is not None:
        user.username = user_data.username
    if user_data.password is not None:
        user.password = hash_password(user_data.password)
    if user_data.money is not None:
        user.money = user_data.money
        
    db.commit()
    db.refresh(user)
    return user

@users_router.delete("/users/{id}")
def delete_users(id: int, request: Request, db:Session = Depends(get_db)):
    require_admin(request, db)
    user = db.query(User).filter(User.id == id).first()  
    if not user:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return id
