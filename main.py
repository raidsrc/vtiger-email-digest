from fastapi import Depends, FastAPI, HTTPException, Request, status, APIRouter
from datetime import datetime, date
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from pymongo.database import Database
from typing import Annotated, TypedDict, Any
import requests
import json
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from routers import actions

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

