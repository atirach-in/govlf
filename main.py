import os
from fastapi import FastAPI
from routers import file
from controllers.corn import start_scheduler

app = FastAPI()

@app.on_event("startup")
def startup_event():
    start_scheduler()

# include routers
app.include_router(file.router, prefix="/file")