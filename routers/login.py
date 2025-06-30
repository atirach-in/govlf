from jose import jwt
from pydantic import BaseModel
import json
from passlib.context import CryptContext
import os
from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
expire = int(expire)
secret = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")

router = APIRouter()

class User(BaseModel):
    username: str
    password: str

@router.get("/{password}")
def get_users(password : str):
    hash = get_password_hash(password)
    print("MD5 Hash:", hash)
    return {"message": hash}

@router.post("/")
def login(user: User): 
    
    print("Current working directory:", os.getcwd())
    with open("users.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for row in data:
        # print(row["username"], row["password"])
        
        if user.username==row["username"]:
            result = verify_password(user.password,row['password'])
            if result :
                print("Match")
                access_token_expires = timedelta(minutes=expire)
                token = create_access_token(data={"sub": row["username"]}, expires_delta=access_token_expires)
                
                with open("access-token.json", "r") as f:
                    accessToken = json.load(f)
                    accessToken.append(token)
                    
                with open("access-token.json", "w") as f:
                    json.dump(accessToken, f, indent=4)  # indent เพื่อให้ดูสวย
                
                return {
                    "success" : True,
                    "token" : token
                }


    return {
        "success" : False
    }

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ฟังก์ชันทดสอบ hashing password
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# jwt token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt

