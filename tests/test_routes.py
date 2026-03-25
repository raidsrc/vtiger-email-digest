"""
imma keep it 100, this app is so small. i'm not gonna bother writing tests for the routes. i'm very sure that they work. plus then i'd have to do testing with the database and either mock the db calls or set up a temporary docker container with mongodb running for testing and that would mean i'd have to rewrite my routes to put another layer of abstraction between my app and the db calls and i'm NOT DOING THAT!
"""

"""
wait a sec
testing idea: spin up a docker container containing a mongodb instance, populate it with sample data, give env vars to the app to make it connect to that instance, run it in github actions, run tests, destroy everything when done

i'm cooking
"""

import pytest
import requests
from app.routers.actions import add_project_to_queue, trigger_email
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
                "cf_project_clonename": "c",
                "cf_project_lotnumber": "123",
                "project_no": "PROJ983274298",
                "cf_project_quotenumber": "VVK198237",
                "description": "",
                "cf_project_aavname": "",
                "behind_schedule": "",
                "modifiedtime": "100000",
            },
            {
                "upserted": False,
                "behind_schedule": False,
                "project_name": "Started Project 123",
                "modified_time": "100000",
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
                "modified_time": "2000-01-01 07:00:00",  # because it converts from utc to houston time. remember.
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
                "description": "some description!",
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


class VtigerGetSingleProjectInfoByProjectNumberMockResponse:
    @staticmethod
    def json():
        return {
            "success": True,
            "result": []
        }

    @staticmethod
    def raise_for_status():
        return None


class PostmarkSendEmailMockResponse:
    @staticmethod
    def json():
        return {
            "ErrorCode": 0,
            "Message": "OK",
            "MessageID": "sdf09a8sd90f8a09dsf8a90sd8fa09ds",
            "SubmittedAt": "2005-05-05T05:05:05.0550505Z",
            "To": "a@a.com,b@b.com",
        }


@pytest.mark.parametrize(
    "results_to_check",
    [
        (
            # first email triggered
            {
                "new_sf9_count": 1,
                "new_cloning_count": 3,
                "new_dna_count": 2,
                "old_sf9_count": 0,
                "old_cloning_count": 1,
                "old_dna_count": 1,

                "new_projects_count": 10,
                "old_projects_count": 6,
                "emailed_about_2_count": 0,
            }
        ),
        (
            # second email triggered
            {
                "new_sf9_count": 0,
                "new_cloning_count": 0,
                "new_dna_count": 0,
                "old_sf9_count": 1,
                "old_cloning_count": 4,
                "old_dna_count": 3,

                "new_projects_count": 0,
                "old_projects_count": 10,
                "emailed_about_2_count": 6,
            }
        ),
    ],
)
def test_trigger_email(monkeypatch, results_to_check):
    # call the function and get the return value
    # check the return value's lists to see length for count of projects
    # count emailed_about: 0 and emailed_about: 1 for all new projects lists
    # same for old proj lists

    def mock_post(*args, **kwargs):
        return PostmarkSendEmailMockResponse()

    monkeypatch.setattr(requests, "post", mock_post)

    def mock_get(*args, **kwargs):
        return VtigerGetSingleProjectInfoByProjectNumberMockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    trigger_email_response = trigger_email()
    assert trigger_email_response["email_response"]["ErrorCode"] == 0
    assert len(trigger_email_response["new_projects_sf9"]) == results_to_check["new_sf9_count"]
    assert len(trigger_email_response["new_projects_cloning"]) == results_to_check["new_cloning_count"]
    assert len(trigger_email_response["new_projects_dna"]) == results_to_check["new_dna_count"]
    assert len(trigger_email_response["old_projects_sf9"]) == results_to_check["old_sf9_count"]
    assert len(trigger_email_response["old_projects_cloning"]) == results_to_check["old_cloning_count"]
    assert len(trigger_email_response["old_projects_dna"]) == results_to_check["old_dna_count"]


    assert trigger_email_response["new_projects_count"] == results_to_check["new_projects_count"]
    assert trigger_email_response["old_projects_count"] == results_to_check["old_projects_count"]
    assert trigger_email_response["emailed_about_2_count"] == results_to_check["emailed_about_2_count"]
    


# save this one for last
def test_clear_queue():
    pass
