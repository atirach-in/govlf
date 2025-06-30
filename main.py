from fastapi import FastAPI
from routers import file, login
from middleware.verify_token import SimpleMiddleware  

app = FastAPI()

# เพิ่ม Middleware เข้าแอป
app.add_middleware(SimpleMiddleware)

# include routers
app.include_router(file.router, prefix="/file")
app.include_router(login.router, prefix="/login")
