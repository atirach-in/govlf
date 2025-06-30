from fastapi import  Request
from starlette.middleware.base import BaseHTTPMiddleware
from jose import JWTError, jwt
from dotenv import load_dotenv
import os
from fastapi.responses import JSONResponse

# โหลด .env
load_dotenv()

# ดึงตัวแปร .env
secret = os.getenv("SECRET_KEY")
algorithm = os.getenv("ALGORITHM")
class SimpleMiddleware(BaseHTTPMiddleware):

    @staticmethod
    def verify_jwt_token(token: str):
        try:
            payload = jwt.decode(token, secret, algorithms=[algorithm])
            return payload
        except JWTError:
            return None  # คืน None ถ้า token ผิด

    async def dispatch(self, request: Request, call_next):
        print("ก่อนจะถึง endpoint")

        if not request.url.path.startswith("/login"):
            auth = request.headers.get("Authorization")
            if auth is None or not auth.startswith("Bearer "):
                return JSONResponse(status_code=401, content={"detail": "ไม่มี Bearer token"})

            token = auth.split(" ")[1]
            payload = SimpleMiddleware.verify_jwt_token(token)

            if not payload:
                return JSONResponse(status_code=401, content={"detail": "Token ไม่ถูกต้อง"})

        response = await call_next(request)
        print("หลังจากออกจาก endpoint")
        return response