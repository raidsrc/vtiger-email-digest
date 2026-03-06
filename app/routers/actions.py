from typing import List

from fastapi import Depends, APIRouter
from datetime import datetime, date
import os
from pymongo import MongoClient
from pymongo.database import Database
import requests
import json
from app.deps import get_current_username
from app.class_types import (
    ProjectRequestBody,
    ProjectWrapperMongo,
)
from app.helper import (
    split_projects_list_by_activities,
    get_project_info_from_vtiger_by_number,
    convert_UTC_to_houston,
)


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
# not throwing error if these ones are empty string because they should be allowed to be empty string


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
            "projectstatus": project.projectstatus or "",
            "cf_project_activities": project.cf_project_activities or "",
            "projectname": project.projectname or "",
            "cf_project_clonename": project.cf_project_clonename or "",
            "cf_project_lotnumber": project.cf_project_lotnumber or "",
            "project_no": project.project_no or "",
            "cf_project_quotenumber": project.cf_project_quotenumber or "",
            "description": project.description or "",
            "cf_project_aavname": project.cf_project_aavname or "",
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
    default behavior is to clear only the projects where emailed_about == 2.
    """
    projects: list[ProjectWrapperMongo] = []
    if all == True:
        projectsCursor = db_queue_collection.find()  # all projects
    else:
        if emailed_about == 0:
            projectsCursor = db_queue_collection.find(
                {"emailed_about": 0}
            )  # just arrived, not emailed projects
        elif emailed_about == 1:
            projectsCursor = db_queue_collection.find(
                {"emailed_about": 1}
            )  # emailed 1x projects
        else:
            projectsCursor = db_queue_collection.find(
                {"emailed_about": 2}
            )  # emailed 2x projects

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
        elif emailed_about == 1:
            query_filter = {"emailed_about": 1}
            db_queue_collection.delete_many(query_filter)
        else:
            query_filter = {"emailed_about": 2}
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
    trigger a project digest email to be sent.
    get updated data on all of the older projects first, though.
    increment all documents' emailed_about by 1.
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
    # both lists are now sorted by activities
    # fetch updated data from vtiger on all the old projects, then add that data to those old projects
    for old_project in old_projects:
        full_data = get_project_info_from_vtiger_by_number(old_project["project_no"])
        if full_data is None:  # if no project data came back
            continue  # skip it whatever
        old_project["id"] = full_data["id"]
        old_project["modifiedtime"] = convert_UTC_to_houston(full_data["modifiedtime"])
        old_project["createdtime"] = convert_UTC_to_houston(full_data["createdtime"])
    # now old projects list is updated with some more stuff

    # need to split them into a bunch of different lists by activities
    # i'll just do the main ones and then other. sf9, hek293, cloning, dna, assay, task, other.
    new_dict = split_projects_list_by_activities(new_projects)
    old_dict = split_projects_list_by_activities(old_projects)

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
            "new_projects_sf9": new_dict["sf9"],
            "new_projects_hek293": new_dict["hek293"],
            "new_projects_cloning": new_dict["cloning"],
            "new_projects_dna": new_dict["dna"],
            "new_projects_task": new_dict["task"],
            "new_projects_assay": new_dict["assay"],
            "new_projects_other": new_dict["other"],
            "new_projects_count": len(new_projects),
            "old_projects_sf9": old_dict["sf9"],
            "old_projects_hek293": old_dict["hek293"],
            "old_projects_cloning": old_dict["cloning"],
            "old_projects_dna": old_dict["dna"],
            "old_projects_task": old_dict["task"],
            "old_projects_assay": old_dict["assay"],
            "old_projects_other": old_dict["other"],
            "old_projects_count": len(old_projects),
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
        "new_projects_sf9": new_dict["sf9"],
        "new_projects_hek293": new_dict["hek293"],
        "new_projects_cloning": new_dict["cloning"],
        "new_projects_dna": new_dict["dna"],
        "new_projects_task": new_dict["task"],
        "new_projects_assay": new_dict["assay"],
        "new_projects_other": new_dict["other"],
        "new_projects_count": len(new_projects),
        "old_projects_sf9": old_dict["sf9"],
        "old_projects_hek293": old_dict["hek293"],
        "old_projects_cloning": old_dict["cloning"],
        "old_projects_dna": old_dict["dna"],
        "old_projects_task": old_dict["task"],
        "old_projects_assay": old_dict["assay"],
        "old_projects_other": old_dict["other"],
        "old_projects_count": len(old_projects),
        "email_response": rbody,
    }
