from fastapi import FastAPI
from datetime import datetime
import sqlite3

app = FastAPI()
connection = sqlite3.connect("db.db")
cursor = connection.cursor()

@app.get("/")
def read_root():
    now_str = str(datetime.now())
    return {"name": "vtiger-email-digest", "date": now_str, "hello": "world"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/test-endpoint/{number}")
def read_item_2(number: int, q: str | None = None):
    number_squared = number**2
    response_q: str = ""
    if q is None:
        response_q = "q is empty."
    else:
        response_q = q
    return {"your_number_squared": number_squared, "response_q": response_q}


# view projects currently in queue (not sent yet)
@app.get("/actions/projects/queue")
def view_queue():
    # get all the projects in the queue
    # return them
    return 0


# add a project to the projects queue.
@app.post("/actions/projects/queue")
def add_project_to_queue():
    return 0


# clear the queue.
@app.delete("/actions/projects/queue")
def clear_queue():
    return 0


# view current email settings.
@app.get("/actions/projects/email")
def view_email_settings():
    return 0


# trigger an email to be sent.
@app.post("/actions/projects/email")
def trigger_email():
    return 0
