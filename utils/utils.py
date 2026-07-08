import json
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta, timezone

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "SECRET_KEY"

def read_json(file_path):
    with open(file_path, "r") as file:
        content = file.read()

        return json.loads(content)
    
def write_json(file_path, content):
    with open(file_path, "w") as f:
        json.dump(content, f)
        return content
    
def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=15
    )

    to_encode.update({"exp": expire})

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm="HS256"
    )

    return token