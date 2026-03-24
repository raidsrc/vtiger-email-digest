"""
imma keep it 100, this app is so small. i'm not gonna bother writing tests for the routes. i'm very sure that they work. plus then i'd have to do testing with the database and either mock the db calls or set up a temporary docker container with mongodb running for testing and that would mean i'd have to rewrite my routes to put another layer of abstraction between my app and the db calls and i'm NOT DOING THAT!
"""

pass


"""
wait a sec
testing idea: spin up a docker container containing a mongodb instance, populate it with sample data, give env vars to the app to make it connect to that instance, run it in github actions, run tests, destroy everything when done

i'm cooking
"""

from app.routers.actions import add_project_to_queue
from app.class_types import ProjectRequestBody


def test_something():
    args1 = {
        "projectstatus": "status",
        "cf_project_activities": "Started",
        "projectname": "Started Project 123",
        "cf_project_clonename": "",
        "cf_project_lotnumber": "",
        "project_no": "",
        "cf_project_quotenumber": "",
        "description": "",
        "cf_project_aavname": "",
        "behind_schedule": "",
        "modifiedtime": "",
    }
    p1 = ProjectRequestBody(**args1)
    return1 = add_project_to_queue(p1)
    assert return1.get('success') == True 
    assert return1.get('upserted') == False 
    return_doc1 = return1.get("document_added_to_database")
    assert return_doc1 is not None
    assert return_doc1["project"]["projectname"] == "Started Project 123"
