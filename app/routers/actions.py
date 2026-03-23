from fastapi import Depends, APIRouter
from datetime import datetime, date
import os
from pymongo import MongoClient
from pymongo.database import Database
import requests
import json
from zoneinfo import ZoneInfo
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

MONGO_URI_PREFIX = os.getenv("MONGO_URI_PREFIX") or ""
MONGO_URI_ADDRESS = os.getenv("MONGO_URI_ADDRESS") or ""
MONGO_USERNAME = os.getenv("MONGO_USERNAME") or ""
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD") or ""
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
if QUEUE_COLLECTION == "":
    raise Exception("QUEUE_COLLECTION missing")
if TRASH_COLLECTION == "":
    raise Exception("TRASH_COLLECTION missing")

uri = f"{MONGO_URI_PREFIX}{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_URI_ADDRESS}"
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
    behind_schedule: bool | None = None,
):
    """
    view all projects currently in queue
    default behavior is to get all projects
    if ?emailed_about=0 view all projects not emailed about yet
    if ?emailed_about=1 view all projects emailed about once
    if ?behind_schedule=true view projects that are behind schedule
    """
    projects: list[ProjectWrapperMongo] = []
    query_filter = {}
    if emailed_about is not None:
        query_filter["emailed_about"] = emailed_about
    if behind_schedule is not None:
        query_filter["behind_schedule"] = behind_schedule
    projectsCursor = db_queue_collection.find(query_filter)

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

    UTC = ZoneInfo("UTC")
    now_utc = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
    now_houston_time = convert_UTC_to_houston(now_utc)
    # be ready for behind_schedule coming from vtiger workflow to be a string or a bool or none.
    behind_schedule = (
        True
        if project.behind_schedule == "true" or project.behind_schedule is True
        else False
    )
    document_to_insert = {
        "datetime_received": now_utc,
        "emailed_about": 0,
        "behind_schedule": behind_schedule,
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
            "vtiger_email_digest_received_datetime_houston": now_houston_time,
            "modifiedtime": project.modifiedtime or "",
        },
    }
    # if behind schedule, upsert. if a behind schedule project with this project_no already exists in the queue, replace it with the new data. otherwise, it's new so insert as normal.
    upserted: bool = False
    if behind_schedule is True:
        document_to_upsert = document_to_insert  # just so i'm clear on what it is.
        # update the modified time with the new value sent from vt
        document_to_upsert["project"]["modifiedtime"] = (
            convert_UTC_to_houston(project.modifiedtime) or ""
        )
        # match project number and behind schedule
        query_filter = {
            "project.project_no": project.project_no,
            "behind_schedule": True,
        }
        replace_return = db_queue_collection.replace_one(query_filter, document_to_upsert, upsert=True)  # type: ignore
        # there is no did_upsert. for some reason the autocompletion and the pymongo docs are wrong.
        # there is an updatedExisting property on the raw_result, though. using that.
        raw_result = replace_return.raw_result
        assert raw_result is not None
        upserted = raw_result["updatedExisting"]
    else:
        db_queue_collection.insert_one(document_to_insert)  # type: ignore
    # document_to_insert["_id"] = str(document_to_insert["_id"])
    response = {
        "success": True,
        "upserted": upserted,
        "document_added_to_database": document_to_insert,
    }
    return response


@actions_router.delete("/projects/queue")
def clear_queue(
    emailed_about: int | None = None,
    all_projects: bool | None = None,
    behind_schedule: bool | None = False,
):
    """
    remove projects from queue. this means moving projects from projectQueue into projectQueueTrash.
    default behavior is to clear only the projects where emailed_about >= 2.
    if all_projects is true, delete all projects
    if behind_schedule is true, delete those that are behind schedule
    """

    projects: list[ProjectWrapperMongo] = []
    query_filter = {}
    if emailed_about is not None:
        query_filter["emailed_about"] = emailed_about
    else:
        query_filter["emailed_about"] = {"$gte: 2"}
    if behind_schedule is not None:
        query_filter["behind_schedule"] = behind_schedule
    if all_projects is True:
        query_filter = {}

    projectsCursor = db_queue_collection.find(query_filter)

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
    # get projects that are not behind schedule that have been emailed about 0 times or 1 time.
    new_projects = [
        p["project"]
        for p in projects
        if p.get("emailed_about") == 0 and p.get("behind_schedule") is not True
        # use .get in dictionaries to avoid KeyError if it doesn't exist
    ]
    old_projects = [
        p["project"]
        for p in projects
        if p.get("emailed_about") == 1 and p.get("behind_schedule") is not True
    ]
    # get projects that are behind schedule
    behind_schedule_projects = [
        p.get("project") for p in projects if p.get("behind_schedule") is True
    ]
    # lists are now sorted by activities
    # fetch updated data from vtiger on all the old projects, then add that data to those old projects
    for old_project in old_projects:
        full_data = get_project_info_from_vtiger_by_number(old_project["project_no"])
        if full_data is None:  # if no project data came back
            continue  # skip it whatever
        # update fields with new data
        old_project["projectstatus"] = full_data["projectstatus"]
        old_project["projectname"] = full_data["projectname"]
        old_project["cf_project_clonename"] = full_data["cf_project_clonename"]
        old_project["cf_project_aavname"] = full_data["cf_project_aavname"]
        # and add the other stuff
        old_project["id"] = full_data["id"]
        old_project["modifiedtime"] = convert_UTC_to_houston(full_data["modifiedtime"])
        old_project["createdtime"] = convert_UTC_to_houston(full_data["createdtime"])
    # now old projects list is updated with some more stuff

    # need to split them into a bunch of different lists by activities
    # i'll just do the main ones and then other. sf9, hek293, cloning, dna, assay, task, other.
    new_dict = split_projects_list_by_activities(new_projects)
    old_dict = split_projects_list_by_activities(old_projects)

    # as for the behind schedule projects: i'll just dump them all into a single table. there shouldn't be that many of them anyway. no further processing needed.

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
        "TemplateAlias": "digest-template-2",
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
            "behind_schedule_projects": behind_schedule_projects,
            "behind_schedule_projects_count": len(behind_schedule_projects),
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
        "behind_schedule_projects": behind_schedule_projects,
        "behind_schedule_projects_count": len(behind_schedule_projects),
        "email_response": rbody,
    }
