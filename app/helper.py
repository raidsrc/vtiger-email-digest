from typing import List, Dict, Literal
import os
import requests
import base64
from app.class_types import Project, VtigerGetProjectResponse
from datetime import datetime
from zoneinfo import ZoneInfo


def split_projects_list_by_activities(projects_list: List[Project]):
    """
    take list of projects and split into dict of lists of projects based on activities
    return type is a dict with keys str and values lists of projects of 1 activities type
    """
    activities_dict: Dict[str, List[Project | None]] = {
        "sf9": [],
        "hek293": [],
        "cloning": [],
        "dna": [],
        "task": [],
        "assay": [],
        "other": [],
    }
    for p in projects_list:
        if p["cf_project_activities"] == "SF9":
            activities_dict["sf9"].append(p)
        elif p["cf_project_activities"] == "HEK293":
            activities_dict["hek293"].append(p)
        elif p["cf_project_activities"] == "CLONING":
            activities_dict["cloning"].append(p)
        elif p["cf_project_activities"] == "DNA":
            activities_dict["dna"].append(p)
        elif p["cf_project_activities"] == "TASK":
            activities_dict["task"].append(p)
        elif p["cf_project_activities"] == "ASSAY":
            activities_dict["assay"].append(p)
        else:
            activities_dict["other"].append(p)
    return activities_dict


def get_project_info_from_vtiger_by_number(project_number: str):
    """
    given one project number (PROJ####), fetch its data from vtiger.
    return dict containing all the info.
    """
    user = os.getenv("VT_USER") or ""
    accesskey = os.getenv("VT_ACCESSKEY") or ""
    to_enc = f"{user}:{accesskey}".encode("utf-8")
    enc = base64.b64encode(to_enc)
    dec = enc.decode("utf-8")
    headers = {
        "Authorization": f"Basic {dec}",
    }
    try:
        r = requests.get(
            f"https://virovek.od2.vtiger.com/restapi/vtap/api/get-single-project-info?projectnumber={project_number}",
            headers=headers,
        )
        if r.status_code != requests.codes.ok:  # if not good http code
            r.raise_for_status()
        # otherwise parse body
        r_body: VtigerGetProjectResponse = r.json()
        result = r_body.result
        if len(result) == 0:
            print("No projects match this project number.")
            return None
        project = r_body.result[0]
        return project
    except requests.ConnectionError:
        print(
            f"ConnectionError in get_project_info_from_vtiger_by_number for {project_number}."
        )
        return None
    except requests.HTTPError:
        print(
            f"HTTPError in get_project_info_from_vtiger_by_number for {project_number}."
        )
        return None
    except requests.JSONDecodeError:
        print(
            f"JSONDecodeError in get_project_info_from_vtiger_by_number for {project_number}."
        )
        return None
    finally:
        print(f"Finally block run in get_project_info_from_vtiger_by_number for {project_number}.")
        return None


def convert_UTC_to_houston(date_time: str | None):
    """
    given string that looks like "2026-03-03 16:48:40" and knowing that it's UTC, convert it to houston time
    """
    if date_time is None or "":
        return ""
    utc = datetime.fromisoformat(f"{date_time}Z")
    chicago_zone = ZoneInfo("America/Chicago")
    new_time = utc.astimezone(chicago_zone)
    return new_time.strftime("%Y-%m-%d %H:%M:%S")
