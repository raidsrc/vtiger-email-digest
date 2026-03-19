from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from fastapi.security import HTTPBasic
from app.routers import actions

load_dotenv()
app = FastAPI()
security = HTTPBasic()

app.include_router(actions.actions_router, prefix="/api/actions")


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
