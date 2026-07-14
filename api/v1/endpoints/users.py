from fastapi import APIRouter, Depends
from database import get_db, Base
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String


users_router = APIRouter()


# class UserCreate(BaseModel): # validation
#       username: str = Field(min_length=6, max_length=20)
#       password: str = Field(min_length=8, max_length=16)
#       model_config = ConfigDict(from_attributes=True)

# class UserUpdate(BaseModel):
#     username: str | None = Field(default=None, min_length=6, max_length=20)
#     password: str | None = Field(default=None, min_length=8, max_length=16)


# @users_router.post("/users")
# def create_user(user: UserCreate, db:Session = Depends(get_db)):
#     new_user = User(username = user.username, password = user.password)
#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)
#     return new_user

# @users_router.get("/users/{id}")
# def get_user(id, db:Session = Depends(get_db)):
#    user = db.query(User).filter(User.id == id).first()
#    return user

# @users_router.get("/users")
# def get_users(db:Session = Depends(get_db)):
#    user = db.query(User).all()
#    return user

# @users_router.put("/users")
# def update_users(id: str, user_data: UserUpdate, db:Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == id).first()  

#     if user_data.username is not None:
#         user.username = user_data.username
#     if user_data.password is not None:
#         user.password = user_data.password 
#     db.commit()
#     db.refresh(user)
#     return user

# @users_router.delete("/users/{id}")
# def delete_users(id: int, db:Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == id).first()  
#     db.delete(user)
#     db.commit()
#     return id