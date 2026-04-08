import os

from fastapi import FastAPI
from datetime import datetime
from dotenv import load_dotenv
from fastapi.security import HTTPBasic
from contextlib import asynccontextmanager
from loguru import logger
from datetime import datetime
import os
from app.db import DatabaseLayer
from app.helper import convert_UTC_to_houston, get_now_UTC_string
from app.routers import api
from app.db_setup import db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # set up logger
    LOGS_DIR_PATH = os.getenv("LOGS_DIR_PATH") or ""
    if LOGS_DIR_PATH == "":
        raise Exception("LOGS_DIR_PATH missing")
    now_houston = convert_UTC_to_houston(get_now_UTC_string())
    now_houston = now_houston.replace(" ", "--").replace(
        ":", "-"
    )  # replace characters to make this a valid filename
    logfile_name = f"logfile_{now_houston}.log"
    logfile_path_and_name = os.path.join(LOGS_DIR_PATH, logfile_name)
    logger.add(logfile_path_and_name, rotation="0:00")
    # alright. my logger will send message to both stderr and to a file.

    # gather db config env vars
    MONGO_URI_PREFIX = os.getenv("MONGO_URI_PREFIX") or ""
    MONGO_URI_ADDRESS = os.getenv("MONGO_URI_ADDRESS") or ""
    MONGO_USERNAME = os.getenv("MONGO_USERNAME") or ""
    MONGO_PASSWORD = os.getenv("MONGO_PASSWORD") or ""
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME") or ""
    QUEUE_COLLECTION = os.getenv("QUEUE_COLLECTION") or ""
    TRASH_COLLECTION = os.getenv("TRASH_COLLECTION") or ""
    if MONGO_URI_PREFIX == "":
        raise Exception("MONGO_URI_PREFIX missing")
    if MONGO_URI_ADDRESS == "":
        raise Exception("MONGO_URI_ADDRESS missing")
    if MONGO_USERNAME == "":
        raise Exception("MONGO_USERNAME missing")
    if MONGO_PASSWORD == "":
        raise Exception("MONGO_PASSWORD missing")
    if MONGO_DB_NAME == "":
        raise Exception("MONGO_DB_NAME missing")
    if QUEUE_COLLECTION == "":
        raise Exception("QUEUE_COLLECTION missing")
    if TRASH_COLLECTION == "":
        raise Exception("TRASH_COLLECTION missing")

    database_layer = DatabaseLayer(
        MONGO_URI_PREFIX,
        MONGO_URI_ADDRESS,
        MONGO_USERNAME,
        MONGO_PASSWORD,
        MONGO_DB_NAME,
        QUEUE_COLLECTION,
        TRASH_COLLECTION,
    )
    database_layer.connect()
    db = database_layer
    db.queue_collection = 
    db.trash_collection = 

    logger.info("======== VTIGER EMAIL DIGEST SERVER ========")
    logger.info("app initialized successfully.")

    yield
    database_layer.close()


# load env vars and set up app
load_dotenv()
app = FastAPI(lifespan=lifespan)
security = HTTPBasic()


app.include_router(api.api_router, prefix="/api")


@app.get("/")
@app.get("/api")
def read_root():
    logger.info("GET -> /api")
    now = datetime.now()
    now_str = str(now)
    return {
        "name": "vtiger-email-digest",
        "date": now_str,
        "timezone": str(now.astimezone().tzname()),
        "hello": "world",
    }
