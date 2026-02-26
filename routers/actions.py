from fastapi import Depends, APIRouter
from datetime import datetime, date
from pydantic import BaseModel
import os
from pymongo import MongoClient
from pymongo.database import Database
from typing import TypedDict
import requests
import json
from deps import get_current_username
from class_types import Project, ProjectRequestBody, ProjectWrapperMongo


MONGO_PASSWORD = os.getenv("MONGO_PASSWORD") or ""
QUEUE_COLLECTION = os.getenv("QUEUE_COLLECTION") or ""
TRASH_COLLECTION = os.getenv("TRASH_COLLECTION") or ""
if MONGO_PASSWORD == "":
    raise Exception("MONGO_PASSWORD missing")
if QUEUE_COLLECTION == "":
    raise Exception("QUEUE_COLLECTION missing")
if TRASH_COLLECTION == "":
    raise Exception("TRASH_COLLECTION missing")

uri = f"mongodb+srv://admin:{MONGO_PASSWORD}@cluster0.ps7aafk.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client: MongoClient[ProjectWrapperMongo] = MongoClient(uri)
db: Database[ProjectWrapperMongo] = client["vtigerEmailDigestDatabase"]
db_queue_collection = db[QUEUE_COLLECTION]
db_trash_collection = db[TRASH_COLLECTION]

EMAIL_SETTINGS_RECIPIENTS = os.getenv("EMAIL_SETTINGS_RECIPIENTS") or ""
EMAIL_SETTINGS_CC = os.getenv("EMAIL_SETTINGS_CC") or ""
EMAIL_SETTINGS_BCC = os.getenv("EMAIL_SETTINGS_BCC") or ""
POSTMARK_SERVER_TOKEN = os.getenv("POSTMARK_SERVER_TOKEN") or ""
# not checking if these ones are empty string or not because they should be allowed to be empty string


actions_router = APIRouter(dependencies=[Depends(get_current_username)])


@actions_router.get("/projects/queue")
def view_queue(
    emailed_about: int | None = None,
):
    """
    view all projects currently in queue
    if ?emailed_about=0 view all projects not emailed about yet
    if ?emailed_about=1 view all projects emailed about once
    """
    projects: list[ProjectWrapperMongo] = []
    if emailed_about == 0:
        projectsCursor = db_queue_collection.find(
            {"emailed_about": 0}
        )  # not emailed projects
    elif emailed_about == 1:
        projectsCursor = db_queue_collection.find(
            {"emailed_about": 1}
        )  # emailed 1x projects
    else:
        projectsCursor = db_queue_collection.find()  # all projects

    for project in projectsCursor:
        oid = str(project["_id"])
        project["_id"] = oid
        projects.append(project)
    projects = sorted(
        projects, key=lambda project: project["project"]["cf_project_activities"]
    )  # sort list of all projects by activities

    return projects


@actions_router.post("/projects/queue")
async def add_project_to_queue(project: ProjectRequestBody):
    """
    add a project to the projects queue.
    """
    # when post req received, first validate it
    # break down the body into all the pieces and assign to vars
    # write to db with datetime received
    # return that the data has been written to db successfully

    now = datetime.now()
    document_to_insert = {
        "datetime_received": str(now),
        "timezone": str(now.astimezone().tzname()),
        "emailed_about": 0,
        "project": {
            "contactid": project.contactid,
            "projectstatus": project.projectstatus,
            "cf_project_activities": project.cf_project_activities,
            "projectname": project.projectname,
            "linktoaccountscontacts": project.linktoaccountscontacts,
            "cf_project_clonename": project.cf_project_clonename,
            "cf_project_lotnumber": project.cf_project_lotnumber,
            "project_no": project.project_no,
            "cf_project_laststatuschange": project.cf_project_laststatuschange,
            "cf_project_relatedorganization": project.cf_project_relatedorganization,
            "cf_project_usecustomerbuffer": project.cf_project_usecustomerbuffer,
            "cf_project_projectnotesfromquote": project.cf_project_projectnotesfromquote,
            "cf_project_quotenumber": project.cf_project_quotenumber,
            "cf_project_goisize": project.cf_project_goisize,
            "description": project.description,
            "cf_project_aavname": project.cf_project_aavname,
            "cf_project_aavserotype": project.cf_project_aavserotype,
            "cf_project_productionscale": project.cf_project_productionscale,
            "cf_project_concentrationrequirement": project.cf_project_concentrationrequirement,
            "cf_project_buffer": project.cf_project_buffer,
            "cf_project_deliveryvolume": project.cf_project_deliveryvolume,
            "createdtime": project.createdtime,
            "modifiedtime": project.modifiedtime,
            "id": project.id,
            "url": project.url,
        },
    }
    db_queue_collection.insert_one(document_to_insert)  # type: ignore
    document_to_insert["_id"] = str(document_to_insert["_id"])
    response = {
        "success": True,
        "document_added_to_database": document_to_insert,
    }
    return response


@actions_router.delete("/projects/queue")
def clear_queue(emailed_about: int | None = None, all: bool = False):
    """
    remove projects from queue. this means moving projects from projectQueue into projectQueueTrash.
    default behavior is to clear of only the projects where emailed_about == 1.
    """
    projects: list[ProjectWrapperMongo] = []
    if all == True:
        projectsCursor = db_queue_collection.find()  # all projects
    else:
        if emailed_about == 0:
            projectsCursor = db_queue_collection.find(
                {"emailed_about": 0}
            )  # not emailed projects
        else:
            projectsCursor = db_queue_collection.find(
                {"emailed_about": 1}
            )  # emailed 1x projects

    for project in projectsCursor:
        oid = str(project["_id"])
        project["_id"] = oid
        projects.append(project)
    projects = sorted(
        projects, key=lambda project: project["project"]["cf_project_activities"]
    )
    # now projects is list of all chosen projects sorted by activity

    # if no projects, don't do anything
    if len(projects) == 0:
        response = {
            "success": True,
            "documents_trashed": [],
        }
        return response

    # otherwise, delete stuff
    if all == True:
        query_filter = {}
        db_queue_collection.delete_many(query_filter)
    else:
        if emailed_about == 0:
            query_filter = {"emailed_about": 0}
            db_queue_collection.delete_many(query_filter)
        else:
            query_filter = {"emailed_about": 1}
            db_queue_collection.delete_many(query_filter)

    # deletion finished, now to insert into trash collection
    db_trash_collection.insert_many(projects)

    # before returning gotta change ObjectId to string so fastapi doesn't complain
    for project in projects:
        project["_id"] = str(project["_id"])
    response = {
        "success": True,
        "documents_trashed": projects,
    }
    return response


# i will manually delete the projectQueueTrash when I feel like it.


@actions_router.get("/projects/email")
def view_email_settings():
    """
    view current email settings.
    """
    return {
        "EMAIL_SETTINGS_RECIPIENTS": EMAIL_SETTINGS_RECIPIENTS,
        "EMAIL_SETTINGS_CC": EMAIL_SETTINGS_CC,
        "EMAIL_SETTINGS_BCC": EMAIL_SETTINGS_BCC,
    }


@actions_router.post("/projects/email")
def trigger_email():
    """
    trigger an email to be sent. returns an html table with a header, rows corresponding to projects, and columns corresponding to important project fields. separate tables for emailed_about == 0 and == 1. also increments all documents' emailed_about by 1.
    """
    # get projects
    projects: list[ProjectWrapperMongo] = []
    projectsCursor = db_queue_collection.find()
    for project in projectsCursor:
        projects.append(project)
    projects = sorted(
        projects, key=lambda project: project["project"]["cf_project_activities"]
    )
    new_projects = [p["project"] for p in projects if p["emailed_about"] == 0]
    old_projects = [p["project"] for p in projects if p["emailed_about"] == 1]

    # now send a req to tell postmark to send an email
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": f"{POSTMARK_SERVER_TOKEN}",
    }
    data = {
        "From": "noreply@virovek.com",
        "To": EMAIL_SETTINGS_RECIPIENTS,
        "Cc": EMAIL_SETTINGS_CC,
        "MessageStream": "broadcast",
        "TemplateAlias": "digest-template-1",
        "TemplateModel": {
            "today_nice": date.today().strftime("%A, %B %d, %Y"),
            "today_date": str(date.today()),
            "new_projects": new_projects,
            "old_projects": old_projects,
        },
    }
    data = json.dumps(data)
    r = requests.post(
        "https://api.postmarkapp.com/email/withTemplate", headers=headers, data=data
    )
    rbody = r.json()

    # if email sent successfully then increment emailed_about for all projects
    if rbody["ErrorCode"] == 0:
        query_filter = {}
        update_operation = {"$inc": {"emailed_about": 1}}
        db_queue_collection.update_many(query_filter, update_operation)

    return {
        "new_projects": new_projects,
        "old_projects": old_projects,
        "email_response": rbody,
    }


# todo: set a cron job to run at start of work day on mondays, wednesdays, and fridays. send a post to trigger an email to be sent. after that, send delete req to flush queue.
