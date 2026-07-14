from datetime import datetime, timedelta, timezone

from database import get_db, Base

from sqlalchemy.orm import Session

from enum import Enum

from fastapi import (APIRouter, 
                     Depends, 
                     HTTPException,
                     Response,
                     Request)

from pydantic import (BaseModel, 
                      Field, 
                      ConfigDict, 
                      EmailStr)

from sqlalchemy import (Column, 
                        Integer, 
                        String, 
                        ForeignKey, 
                        DateTime,
                        Boolean,
                        Enum as SqlEnum)

from utils.utils import (hash_password, 
                         verify_password, 
                         create_access_token,
                         create_refresh_token,
                         decode_token)

auth_router = APIRouter(prefix="/auth", tags=["Auth"])

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    refresh_token_hash = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    name: str
    price: int = Field(gt=0)
    model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
    name: str | None = None
    price: int | None = Field(default=None, gt=0)


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)

    role = Column(
        SqlEnum(UserRole, name="user_role"),
        default=UserRole.USER,
        nullable=False
    )

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
def login(user_data: UserLogin, response:Response, db: Session = Depends(get_db)):
    hashed_password = hash_password(user_data.password)
    print(hashed_password)
    existing_user = db.query(User).filter(
         (User.username == user_data.username)
    ).first()

    if not existing_user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    
    
    if verify_password(user_data.password, existing_user.password):

        access_token = create_access_token({"sub": str(existing_user.id), "email": existing_user.username})
        refresh_token = create_refresh_token({"sub": str(existing_user.id), "email": existing_user.username})
        
        db_refresh_token = RefreshToken(
            user_id=existing_user.id,
            refresh_token_hash=refresh_token,
            expires_at=datetime.now() + timedelta(days=3),
            revoked=False
        )

        db.add(db_refresh_token)
        db.commit()
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=3*24*60*60
        )
        print(response.headers)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    raise HTTPException(
        status_code=401,
        detail="Invalid password"
    )

@auth_router.post("/refresh")
def refresh_token(refresh_token, db: Session = Depends(get_db)):
    payload = decode_token(refresh_token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    token_type = payload.get("type")

    if token_type != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid token type"
        )
    
    user_id = payload.get("sub")
    username = payload.get("username")
    
    db_token = db.query(RefreshToken).filter(
        RefreshToken.refresh_token_hash == refresh_token,
        RefreshToken.revoked == False
    ).first()

    if not db_token:
        raise HTTPException(status_code=401,
                            detail="Refresh token revoked")

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload"
        )
    
    new_access_token = create_access_token({
         "sub": user_id,
         "username": username
    })

    return {
         "access_token": new_access_token,
         "token_type": "bearer"
    }

@auth_router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        db_token = db.query(RefreshToken).filter(RefreshToken.refresh_token_hash==token).first()
    if db_token:
        db_token.revoked = True
        db.commit()
    response.delete_cookie(key="refresh_token",path="/")
    return {"message":"logout"}