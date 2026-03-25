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
            # not behind schedule
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
            # behind schedule no upsert
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
                "behind_schedule": True,
                "project_name": "Started Project 456",
                "modified_time": "2000-01-01 07:00:00", # because it converts from utc to houston time. remember.
            },
        ),
        (
            # behind schedule yes upsert
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
                "modified_time": "2001-01-01 07:00:00",
            },
        ),
    ],
)
def test_add_project_to_queue(input_project, results_to_check):
    p = ProjectRequestBody(**input_project)
    add_response = add_project_to_queue(p)
    assert add_response["success"] == True
    assert add_response["upserted"] == results_to_check["upserted"]
    assert (
        add_response["document_added_to_database"]["behind_schedule"]
        == results_to_check["behind_schedule"]
    )
    assert (
        add_response["document_added_to_database"]["project"]["projectname"]
        == results_to_check["project_name"]
    )
    assert (
        add_response["document_added_to_database"]["project"]["modifiedtime"]
        == results_to_check["modified_time"]
    )


def test_clear_queue():
    pass
