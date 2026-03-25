"""
imma keep it 100, this app is so small. i'm not gonna bother writing tests for the routes. i'm very sure that they work. plus then i'd have to do testing with the database and either mock the db calls or set up a temporary docker container with mongodb running for testing and that would mean i'd have to rewrite my routes to put another layer of abstraction between my app and the db calls and i'm NOT DOING THAT!
"""

"""
wait a sec
testing idea: spin up a docker container containing a mongodb instance, populate it with sample data, give env vars to the app to make it connect to that instance, run it in github actions, run tests, destroy everything when done

i'm cooking
"""

import pytest
from app.routers.actions import add_project_to_queue
from app.class_types import ProjectRequestBody


@pytest.mark.parametrize(
    "input_project, results_to_check",
    [
        (
            {
                "projectstatus": "Started",
                "cf_project_activities": "DNA",
                "projectname": "Started Project 123",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "PROJ983274298",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "behind_schedule": "",
                "modifiedtime": "",
            },
            {
                "upserted": False,
                "behind_schedule": False,
                "project_name": "Started Project 123",
                "modified_time": "",
            },
        ),
        (
            {
                "projectstatus": "Cloning completed",
                "cf_project_activities": "Cloning",
                "projectname": "Started Project 456",
                "cf_project_clonename": "RAY01",
                "cf_project_lotnumber": "",
                "project_no": "PROJ00000301",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "behind_schedule": True,
                "modifiedtime": "2000-01-01 13:00:00",
            },
            {
                "upserted": False,
                "behind_schedule": False,
                "project_name": "Started Project 456",
                "modified_time": "2000-01-01 13:00:00",
            },
        ),
        (
            {
                "projectstatus": "Cloning completed",
                "cf_project_activities": "Cloning",
                "projectname": "Upserted project",
                "cf_project_clonename": "RAY01",
                "cf_project_lotnumber": "",
                "project_no": "PROJ00000301",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "behind_schedule": True,
                "modifiedtime": "2001-01-01 13:00:00",
            },
            {
                "upserted": True,
                "behind_schedule": True,
                "project_name": "Upserted project",
                "modified_time": "2001-01-01 13:00:00",
            },
        ),
    ],
)
def test_add_project_to_queue(input_project, results_to_check):
    p = ProjectRequestBody(**input_project)
    add_response = add_project_to_queue(p)
    assert add_response.get("success") == True
    assert add_response.get("upserted") == results_to_check.get("upserted")
    assert add_response.get("behind_schedule") == results_to_check.get("behind_schedule")
    assert add_response["project"]["projectname"] == results_to_check.get("project_name")
    assert add_response["project"]["modifiedtime"] == results_to_check.get("modified_time")


def test_add_project_to_queue_1():
    # add not behind schedule not upsert
    args = {
        "projectstatus": "Started",
        "cf_project_activities": "DNA",
        "projectname": "Started Project 123",
        "cf_project_clonename": "",
        "cf_project_lotnumber": "",
        "project_no": "PROJ983274298",
        "cf_project_quotenumber": "",
        "description": "",
        "cf_project_aavname": "",
        "behind_schedule": "",
        "modifiedtime": "",
    }
    p = ProjectRequestBody(**args)
    add_response = add_project_to_queue(p)
    assert add_response.get("success") == True
    assert add_response.get("upserted") == False
    add_response_doc = add_response.get("document_added_to_database")
    assert add_response_doc is not None
    assert add_response_doc["project"]["projectname"] == "Started Project 123"


def test_add_project_to_queue_2():
    # add behind schedule no upsert
    args = {
        "projectstatus": "Cloning completed",
        "cf_project_activities": "Cloning",
        "projectname": "Started Project 456",
        "cf_project_clonename": "RAY01",
        "cf_project_lotnumber": "",
        "project_no": "PROJ00000301",
        "cf_project_quotenumber": "",
        "description": "",
        "cf_project_aavname": "",
        "behind_schedule": True,
        "modifiedtime": "2000-01-01 13:00:00",
    }
    p = ProjectRequestBody(**args)
    add_response = add_project_to_queue(p)
    assert add_response.get("success") == True
    assert add_response.get("upserted") == False
    add_response_doc = add_response.get("document_added_to_database")
    assert add_response_doc is not None
    assert add_response_doc["project"]["projectname"] == "Started Project 456"
    m: str = add_response_doc["project"]["modifiedtime"]
    assert "2000" in m


def test_add_project_to_queue_3():
    # add behind schedule yes upsert
    args = {
        "projectstatus": "Cloning completed",
        "cf_project_activities": "Cloning",
        "projectname": "Upserted project",
        "cf_project_clonename": "RAY01",
        "cf_project_lotnumber": "",
        "project_no": "PROJ00000301",
        "cf_project_quotenumber": "",
        "description": "",
        "cf_project_aavname": "",
        "behind_schedule": True,
        "modifiedtime": "2001-01-01 13:00:00",
    }
    p = ProjectRequestBody(**args)
    add_response = add_project_to_queue(p)
    assert add_response.get("success") == True
    assert add_response.get("upserted") == True
    add_response_doc = add_response.get("document_added_to_database")
    assert add_response_doc is not None
    assert add_response_doc["project"]["projectname"] == "Upserted project"
    assert add_response_doc["project"]["project_no"] == "PROJ00000301"
    m: str = add_response_doc["project"]["modifiedtime"]
    assert "2001" in m


def test_clear_queue():
    pass
