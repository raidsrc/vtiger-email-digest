from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from fastapi.responses import HTMLResponse
from pymongo import MongoClient
from pymongo.database import Database
from typing import TypedDict, Dict

load_dotenv()
app = FastAPI()


class ProjectRequestBody(BaseModel):
    contactid: str
    projectstatus: str
    cf_project_activities: str
    projectname: str
    linktoaccountscontacts: str
    cf_project_clonename: str
    cf_project_lotnumber: str
    project_no: str
    cf_project_laststatuschange: str
    cf_project_relatedorganization: str
    cf_project_usecustomerbuffer: str
    cf_project_projectnotesfromquote: str
    cf_project_quotenumber: str
    cf_project_goisize: str
    description: str
    cf_project_aavname: str
    cf_project_aavserotype: str
    cf_project_productionscale: str
    cf_project_concentrationrequirement: str
    cf_project_buffer: str
    cf_project_deliveryvolume: str
    createdtime: str
    modifiedtime: str
    id: str
    url: str


class Project(TypedDict):
    contactid: str
    projectstatus: str
    cf_project_activities: str
    projectname: str
    linktoaccountscontacts: str
    cf_project_clonename: str
    cf_project_lotnumber: str
    project_no: str
    cf_project_laststatuschange: str
    cf_project_relatedorganization: str
    cf_project_usecustomerbuffer: str
    cf_project_projectnotesfromquote: str
    cf_project_quotenumber: str
    cf_project_goisize: str
    description: str
    cf_project_aavname: str
    cf_project_aavserotype: str
    cf_project_productionscale: str
    cf_project_concentrationrequirement: str
    cf_project_buffer: str
    cf_project_deliveryvolume: str
    createdtime: str
    modifiedtime: str
    id: str
    url: str


MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
uri = f"mongodb+srv://admin:{MONGO_PASSWORD}@cluster0.ps7aafk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client: MongoClient[Project] = MongoClient(uri)
db: Database[Project] = client["vtigerEmailDigestDatabase"]
QUEUE_COLLECTION = os.getenv("QUEUE_COLLECTION") or ""
TRASH_COLLECTION = os.getenv("TRASH_COLLECTION") or ""
db_queue_collection = db[QUEUE_COLLECTION]
db_trash_collection = db[TRASH_COLLECTION]

EMAIL_SETTINGS_RECIPIENTS = os.getenv("EMAIL_SETTINGS_RECIPIENTS")
EMAIL_SETTINGS_CC = os.getenv("EMAIL_SETTINGS_CC")
EMAIL_SETTINGS_BCC = os.getenv("EMAIL_SETTINGS_BCC")


@app.get("/")
def read_root():
    now_str = str(datetime.now())
    return {"name": "vtiger-email-digest", "date": now_str, "hello": "world"}


# view projects currently in queue (not sent yet)
@app.get("/actions/projects/queue")
def view_queue():
    # get all the projects in the queue
    # return them
    return 0


# add a project to the projects queue.
@app.post("/actions/projects/queue")
async def add_project_to_queue(project: ProjectRequestBody):
    # when post req received, break down the body into all the pieces and assign to vars
    # write to db with datetime received
    # return that the data has been written to db successfully

    now = datetime.now()
    data: Dict[str, str | ProjectRequestBody] = {
        "project": project,
        "datetime_received": str(now),
        "timezone": str(now.astimezone().tzname()),
    }
    return data


# clear the queue.
@app.delete("/actions/projects/queue")
def clear_queue():
    # copy all entries in projectQueue into projectQueueTrash
    # delete all entries in projectQueue
    return 0


# i will manually delete the projectQueueTrash when I feel like it.


# view current email settings.
@app.get("/actions/projects/email")
def view_email_settings():
    return {
        "EMAIL_SETTINGS_RECIPIENTS": EMAIL_SETTINGS_RECIPIENTS,
        "EMAIL_SETTINGS_CC": EMAIL_SETTINGS_CC,
        "EMAIL_SETTINGS_BCC": EMAIL_SETTINGS_BCC,
    }


# trigger an email to be sent.
@app.post("/actions/projects/email", response_class=HTMLResponse)
def trigger_email():
    # gather all the projects in the queue into a list
    # sort the list by activities
    # loop through the list
    # for every project, construct an html string

    projects: list[Project] = []

    # # for now, just practicing getting it working. i'm using a local file to test.
    # with open("./many-projects-sample.json") as file:
    #     content = file.read()
    #     projects = json.loads(content)

    projectsCursor = db_queue_collection.find()
    for project in projectsCursor:
        projects.append(project)
    projects = sorted(projects, key=lambda project: project["cf_project_activities"])

    rows_string = ""
    for project in projects:
        needed = {
            "cf_project_activities": project["cf_project_activities"],
            "projectstatus": project["projectstatus"],
            "projectname": project["projectname"],
            "cf_project_clonename": project["cf_project_clonename"],
            "cf_project_aavname": project["cf_project_aavname"],
            "project_no": project["project_no"],
        }
        record_url = project["url"]
        cells_string = ""
        for value in needed.values():
            cell_string = f"<td>{value}</td>"
            cells_string += cell_string
        url_string = f"<td><a href='{record_url}'>Click here.</a></td>"
        row_string = f"<tr>{cells_string}{url_string}</tr>"
        rows_string += row_string

    tableStart = "<table><tbody>"
    tableHead = """<thead>
    <tr>
    <th>Activities</th>
    <th>Status</th>
    <th>Project Name</th>
    <th>Clone Name</th>
    <th>Item Name</th>
    <th>Project Number</th>
    <th>Record URL</th>
    </tr>
    </thead>
    """
    tableEnd = "</tbody></table>"

    return tableStart + tableHead + rows_string + tableEnd


# todo: set a cron job to run at start of work day on mondays, wednesdays, and fridays. send a post to trigger an email to be sent. after that, send delete req to flush queue.
