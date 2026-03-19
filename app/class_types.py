from typing import Dict, List, TypedDict
from pydantic import BaseModel, Field


# what's received from vtiger when the webhook fires
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
    behind_schedule: str | bool | None = "false"
    modifiedtime: str | None = None


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
    id: str | None 
    modifiedtime: str | None
    createdtime: str | None


class VtigerGetProjectResponse(BaseModel):
    success: bool
    result: List[Dict[str, str]]


class ProjectWrapperMongo(TypedDict):
    _id: str  # in the db it's an ObjectId. make sure to convert this to a string before returning in fastapi.
    project: Project
    datetime_received: str
    timezone: str | None
    behind_schedule: bool | None
    emailed_about: (
        int  # if a project is included in a digest email, this counter increments.
    )
