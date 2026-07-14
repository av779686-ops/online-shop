from fastapi import APIRouter, Depends, Request, HTTPException
from database import get_db, Base
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from .auth import User, EmailStr
from utils.utils import decode_token

users_router = APIRouter()


class UserCreate(BaseModel): # validation
      username: str = Field(min_length=6, max_length=20)
      email: str = EmailStr
      password: str = Field(min_length=8, max_length=16)
      model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=6, max_length=20)
    password: str | None = Field(default=None, min_length=8, max_length=16)


@users_router.post("/users")
def create_user(user: UserCreate, request: Request, db:Session = Depends(get_db)):
    token = request.headers.get("authorization").split(" ")[1]
    print(token)
    payload = decode_token(token)
    print("payload--->", payload)

    user_data = db.query(User).filter(User.id == payload["sub"]).first()

    print("Role--->", user_data.role.value)

    if user_data.role.value != "admin":
        raise HTTPException(401, "You are not admin !!!")
    
    new_user = User(username = user.username, email=user.email, password = user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@users_router.get("/users/{id}")
def get_user(id, db:Session = Depends(get_db)):
   user = db.query(User).filter(User.id == id).first()
   return user

@users_router.get("/users")
def get_users(db:Session = Depends(get_db)):
   user = db.query(User).all()
   return user

@users_router.put("/users")
def update_users(id: str, user_data: UserUpdate, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()  

    if user_data.username is not None:
        user.username = user_data.username
    if user_data.password is not None:
        user.password = user_data.password 
    db.commit()
    db.refresh(user)
    return user

@users_router.delete("/users/{id}")
def delete_users(id: int, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()  
    db.delete(user)
    db.commit()
    return id