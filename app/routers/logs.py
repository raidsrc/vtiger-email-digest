import os

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from loguru import logger

from app.deps import get_current_username


log_router = APIRouter(dependencies=[Depends(get_current_username)])


@log_router.get("/logs")
def view_logs():
    """
    return names of all log files.
    """
    logger.info("GET -> /api/logs")
    log_file_list = os.listdir("logs").sort()
    return log_file_list


@log_router.get("/logs/{log_name}", response_class=PlainTextResponse)
def view_log(log_name: str):
    """
    return contents of one particular log file.
    """
    LOGS_DIR_PATH = os.getenv("LOGS_DIR_PATH") or ""
    logger.info(f"GET -> /api/logs/{log_name}")
    log_file_path = os.path.join(LOGS_DIR_PATH, log_name)
    log_file_contents = ""
    with open(log_file_path, "r") as file:
        log_file_contents = file.read()
    return log_file_contents
