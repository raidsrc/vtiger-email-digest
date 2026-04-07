from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from fastapi.security import HTTPBasic
from app.routers import api

# load env vars and set up app
load_dotenv()
app = FastAPI()
security = HTTPBasic()

app.include_router(api.api_router, prefix="/api")


@app.get("/")
@app.get("/api")
def read_root():
    now = datetime.now()
    now_str = str(now)
    return {
        "name": "vtiger-email-digest",
        "date": now_str,
        "timezone": str(now.astimezone().tzname()),
        "hello": "world",
    }
