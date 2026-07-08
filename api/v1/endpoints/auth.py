from database import get_db, Base
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from utils.utils import hash_password, verify_password, create_access_token

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

class UserRegister(BaseModel): # validation
    username: str = Field(min_length=6, max_length=20)
    email: str = EmailStr
    password: str = Field(min_length=8, max_length=16)
    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    username: str = Field(min_length=6, max_length=20)
    password: str = Field(min_length=8, max_length=16)

    model_config = ConfigDict(from_attributes=True)

@auth_router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
         (User.email == user_data.email) | (User.username == user_data.username)
    ).first()

    if existing_user:
        return "We have user with such email or username !!"
    hashed_password = hash_password(user_data.password)

    new_user = User(
         username=user_data.username,
         email=user_data.email,
         password= hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

@auth_router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    hashed_password = hash_password(user_data.password)
    print(hashed_password)
    existing_user = db.query(User).filter(
         (User.username == user_data.username)
    ).first()

    if not existing_user:
        return "We dont have such user !!"
    
    
    if verify_password(user_data.password, existing_user.password):

        access_token = create_access_token({"sub": str(existing_user.id), "email": existing_user.email})
        return {
            "access_token": access_token,
            "email": existing_user.email,
            "id": existing_user.id
        }
    
    return "We dont have such user !!"