from typing import TypedDict
from pydantic import BaseModel


# what's received from vtiger
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


class ProjectWrapperMongo(TypedDict):
    _id: str  # in the db it's an ObjectId. make sure to convert this to a string before returning in fastapi.
    project: Project
    datetime_received: str
    timezone: str
    emailed_about: (
        int  # if a project is included in a digest email, this counter increments.
    )
