from typing import TypedDict
from pydantic import BaseModel, Field


# what's received from vtiger
class ProjectRequestBody(BaseModel):
    projectstatus: str = ""
    cf_project_activities: str = ""
    projectname: str = ""
    cf_project_clonename: str = ""
    cf_project_lotnumber: str = ""
    project_no: str = ""
    cf_project_quotenumber: str = ""
    description: str = ""
    cf_project_aavname: str = ""


class Project(TypedDict):
    projectstatus: str
    cf_project_activities: str
    projectname: str
    cf_project_clonename: str
    cf_project_lotnumber: str
    project_no: str
    cf_project_quotenumber: str
    description: str
    cf_project_aavname: str


class ProjectWrapperMongo(TypedDict):
    _id: str  # in the db it's an ObjectId. make sure to convert this to a string before returning in fastapi.
    project: Project
    datetime_received: str
    timezone: str
    emailed_about: (
        int  # if a project is included in a digest email, this counter increments.
    )
