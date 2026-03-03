from typing import List, Dict
from app.class_types import Project

def split_projects_list_by_activities(projects_list: List[Project]):
  '''
  take list of projects and split into dict of lists of projects based on activities 
  return type is a dict with keys str and values lists of projects of 1 activities type
  '''
  activities_dict: Dict[str, List[Project | None]] = {
    "sf9": [],
    "hek293": [],
    "cloning": [],
    "dna": [],
    "task": [],
    "assay": [],
    "other": []
  }
  for p in projects_list:
    if p["cf_project_activities"] == "sf9":
      activities_dict["sf9"].append(p)
    elif p["cf_project_activities"] == "hek293":
      activities_dict["hek293"].append(p)
    elif p["cf_project_activities"] == "cloning":
      activities_dict["cloning"].append(p)
    elif p["cf_project_activities"] == "dna":
      activities_dict["dna"].append(p)
    elif p["cf_project_activities"] == "task":
      activities_dict["task"].append(p)
    elif p["cf_project_activities"] == "assay":
      activities_dict["assay"].append(p)
    else: 
      activities_dict["other"].append(p)
  return activities_dict
