from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

SECRET_KEY = "dev_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
    })
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        print("DECODED PAYLOAD:", payload)  # 👈 DEBUG

        user_id = payload.get("sub")   # ✅ MUST BE sub

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return payload

    except JWTError as e:
        print("JWT ERROR:", e)  # 👈 VERY IMPORTANT
        raise HTTPException(status_code=401, detail="Invalid token")

