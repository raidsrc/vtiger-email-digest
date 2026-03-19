import pytest
import requests
from app.helper import (
    convert_UTC_to_houston,
    get_project_info_from_vtiger_by_number,
    split_projects_list_by_activities,
)


def test_convert_UTC_to_houston():
    assert convert_UTC_to_houston() == ""
    assert convert_UTC_to_houston("") == ""
    assert convert_UTC_to_houston(None) == ""
    assert convert_UTC_to_houston("2000-02-04 00:00:00") == "2000-02-03 18:00:00"


class VtigerGetSingleProjectInfoByProjectNumberMockResponse:
    @staticmethod
    def json():
        return {
            "success": True,
            "result": [
                {
                    "contactid": "4x26290",
                    "projectstatus": "Invoiced",
                    "cf_project_activities": "SF9",
                    "cf_project_premade": "0",
                    "projectname": "VVK10012822 Project #1",
                    "linktoaccountscontacts": "3x400618",
                    "cf_project_clonename": "UCLA72",
                    "targetenddate": "",
                    "cf_project_lotnumber": "23-398",
                    "assigned_user_id": "19x8",
                    "startdate": "2023-10-05",
                    "project_no": "PROJ4427",
                    "actualenddate": "2023-10-10",
                    "isconvertedfrompotential": "0",
                    "created_user_id": "19x8",
                    "potentialid": "",
                    "source": "WEBSERVICE",
                    "starred": "0",
                    "cf_project_laststatuschange": "2023-12-15",
                    "tags": "",
                    "cf_project_relatedorganization": "",
                    "cf_project_titer": "",
                    "record_currency_id": "",
                    "record_conversion_rate": "",
                    "cf_project_usecustomerbuffer": "0",
                    "cf_project_sendsequenceconfirmation": "1",
                    "cf_project_coadone": "N",
                    "cf_project_projectnotesfromquote": "",
                    "cf_project_quotenumber": "13x308806",
                    "cf_project_coashippeddate": "",
                    "isclosed": "0",
                    "cf_project_cloningassociate": "",
                    "cf_project_associatedqcrecord": "",
                    "modifier_crmid": "",
                    "creator_crmid": "",
                    "cf_project_goisize": "",
                    "cf_project_goisizekb": "",
                    "cf_project_dnasequencing": "0",
                    "description": "23-398: SDS-PAGE showed good VP1 and VP2 on 11/20/23. No re-run",
                    "cf_project_aavname": "AAV6-m5UTR-hcoCD40L",
                    "cf_project_aavserotype": "AAV6 (V290)",
                    "cf_project_productionscale": "1E+13 vg",
                    "cf_project_provideplasmidordnasynthesis": "",
                    "cf_project_concentrationrequirement": "1E+13 vg/ml",
                    "cf_project_shippingmethod": "",
                    "cf_project_dnasequence": "",
                    "cf_project_genenameorgenbank": "",
                    "cf_project_aavdesigngraph": "UCLA72-pFB-m5UTR-hcoCD40L_Map.png",
                    "cf_project_sequencedetails": "UCLA72 from ITR to ITR\ncctgcaggcagctgcgcgctcgctcgctcactgaggccgcccgggcaaagcccgggcgtcgggcgacctttggtcgcccggcctcagtgagcgagcgagcgcgcagagagggagtggccaactccatcactaggggttcctgcggccgcacgcgtcacgcctggaagtgaatgatatgggtgtgatttaaaaaaagaaaaggaaagaaaagaaaagaaaaaccctttacgtaactttttttgctgggacagaagactacgaagcacattttccaggaagtgtgggttgcgacgattgtgcgctcttaactaatcctgagtaaggcggccactttgacagtcttctcatgctgcctctgATGATCGAGACATACAACCAGACCAGCCCCAGAAGCGCCGCCACAGGCCTGCCTATCAGCATGAAGATCTTTATGTACCTGCTGACCGTGTTCCTGATCACCCAGATGATCGGCAGCGCCCTGTTCGCCGTGTACCTGCACAGACGGCTGGACAAGATCGAGGACGAGCGGAACCTGCACGAGGACTTCGTGTTCATGAAGACCATCCAGCGGTGCAACACCGGCGAGAGAAGCCTGAGCCTGCTGAACTGCGAGGAAATCAAGAGCCAGTTCGAGGGCTTCGTGAAGGACATCATGCTGAACAAAGAGGAAACTAAGAAAGAAAACAGCTTCGAGATGCAGAAGGGCGACCAGAACCCCCAGATTGCCGCCCACGTGATCAGCGAGGCCAGCAGCAAGACCACCTCCGTGCTGCAGTGGGCCGAGAAGGGCTACTACACCATGAGCAACAACCTCGTGACCCTGGAAAACGGCAAGCAGCTGACAGTGAAGCGGCAGGGCCTGTACTACATCTACGCCCAAGTGACCTTCTGCAGCAACAGAGAGGCCAGCTCCCAGGCCCCCTTTATCGCCAGCCTGTGCCTGAAGTCCCCCGGCAGATTCGAGAGAATCCTGCTGAGAGCCGCCAACACCCACAGCAGCGCCAAGCCTTGTGGCCAGCAGTCTATCCACCTGGGCGGCGTGTTCGAACTGCAGCCTGGCGCCTCCGTGTTCGTGAACGTGACCGATCCTAGCCAGGTGTCCCACGGCACCGGCTTCACAAGCTTCGGACTGCTGAAGCTGTGAacagtgcgctgtcctaggctgcagcagggctgatgctggcagtcttccctatacagcaagtcagttaggacctgccctgtgttgaactgcctatttataaccctaggatcctcctcatggagaactatttattatgtacccccaaggcacatagagctggaataagagaattacagggcaggcaaaaatcccaagggaccctgctccctaagaacttacaatctgaaacagcaaccccactgattcagacaaccagaaaagacaaagccataatacacagatgacagagctctgatgaaacaacagataactaatgagcacagttttgttgttttatgggtgtgtcgttcaatggacagtgtacttgacttaccagggaagatgcagaagggcaactgtgagcctcagctcacaatctgttatggttgacctgggctccctgcggccctagtaggccaagttctaaagtctcccacggagaattgagaaactctgcctccacctcccccccccataccccaacactcagtatttcaatgtctctactctctctttccctctctcccctccctttcgctccctccctctctcccatctctctctctctctctctctctctctctctctctctctctctctctctctcacacacacacacacacacacagacatacacacacacacacacacacacacagacacacacacacacacacacacacacacacacacggagtcaggctattgttggctggttctcttattatctaccctgtatctgtctacagcactgtcgggtctgtagacaggagctcttggccttcccattcctcctgatggaatgactatatttaaagaaatctgttgtagctccctgaaatctccattgtttccatagtgaacttaatgattatgttattatttattttttgattaataaagaccctctaacattattgttgttgtatagctctcatccaattcccattcttggtcagaagacaccatttcagCTTTCAGTCAGCATGATAGAAACATACAGCCAACCTTCCCCCAGATCCGTGGCAACTGGACTTCCAGCGAGCATGAAGATTTTTATGTATTTACTTACTGTTTTCCTTATCACCCAAATGATTGGATCTGTGCTTTTTGCTGTGTATCTTCATAGAAGATTGGATAAGgtaaggtgacctacaagccttaattagctaaattgggggttcttattgatctaggacggtttgaattaagttctacctaaatgatggagaacagtagaaagtggataatgtttgttgtggcataatgtttgttgcctagaaagtagaaccttacctctgactaagatcttggaatgtgcaatcagacagcctggcttcaaatcttagcttagctcttaactgctctgagattctgcacatgtcacttcatacgtttgtgcggaccgagcggccgcaggaacccctagtgatggagttggccactccctctctgcgcgctcgctcgctcactgaggccgggcgaccaaaggtcgcccgacgcccgggctttgcccgggcggcctcagtgagcgagcgagcgcgcagctgcctgcagg",
                    "cf_project_purificationmethod": "",
                    "cf_project_alertmessageforportal": "",
                    "cf_project_wbtestgraph": "",
                    "cf_project_dnaagarosegel": "",
                    "cf_project_bufferpreference": "",
                    "cf_project_coa": "",
                    "cf_project_createcoa": "0",
                    "cf_project_associatedgeneralcoa": "",
                    "cf_project_shippingconditions": "Dry Ice",
                    "cf_project_rbv": "",
                    "cf_project_buffer": "1xPBS + 0.001% pluronic F-68",
                    "cf_project_capsidrbv": "",
                    "cf_project_dnatype": "",
                    "cf_project_sizeofpcr": "",
                    "cf_project_rbvtype": "",
                    "cf_project_cellstype": "",
                    "cf_project_plasmidcondition": "",
                    "cf_project_aavyield": "",
                    "cf_project_rbvtiter": "",
                    "cf_project_ponumber": "",
                    "cf_project_shippingvia": "UPS Next Day Air",
                    "cf_project_deliveryvolume": "10 x 0.1 ml",
                    "cf_project_a260toa280ratio": "",
                    "targetbudget": "",
                    "projecturl": "",
                    "projectpriority": "",
                    "progress": "",
                    "createdtime": "2023-10-05 14:00:08",
                    "modifiedtime": "2023-12-15 21:11:20",
                    "modifiedby": "19x7",
                    "cf_project_etcfield": "",
                    "id": "31x309014",
                    "imageattachmentids": "31x310378",
                }
            ],
        }

    @staticmethod
    def raise_for_status():
        return None


def test_get_project_info_from_vtiger_by_number(monkeypatch):
    def mock_get(*args, **kwargs):
        return VtigerGetSingleProjectInfoByProjectNumberMockResponse()

    monkeypatch.setattr(requests, "get", mock_get)

    result = get_project_info_from_vtiger_by_number("whatever")
    assert result is not None
    assert result.get("projectstatus") == "Invoiced"


@pytest.fixture
def projects_lists():
    return {
        "project_list_normal": [
            {
                "projectstatus": "",
                "cf_project_activities": "SF9",
                "projectname": "sf9 project",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "HEK293",
                "projectname": "hek293 project 1",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "HEK293",
                "projectname": "hek293 project 2",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "DNA",
                "projectname": "dna project",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "TASK",
                "projectname": "task project",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "ASSAY",
                "projectname": "assay project 1",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "ASSAY",
                "projectname": "assay project 2",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "OTHER",
                "projectname": "other project",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
        ],
        "project_list_empty_string": "",
        "project_list_empty": [],
        "project_list_all_dna": [
            {
                "projectstatus": "",
                "cf_project_activities": "DNA",
                "projectname": "dna project 1",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "DNA",
                "projectname": "dna project 2",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
            {
                "projectstatus": "",
                "cf_project_activities": "DNA",
                "projectname": "dna project 3",
                "cf_project_clonename": "",
                "cf_project_lotnumber": "",
                "project_no": "",
                "cf_project_quotenumber": "",
                "description": "",
                "cf_project_aavname": "",
                "id": "",
                "modifiedtime": "",
                "createdtime": "",
            },
        ],
    }


def test_split_projects_list_by_activities(projects_lists):
    assert split_projects_list_by_activities(
        projects_lists.get("project_list_empty")
    ) == {
        "sf9": [],
        "hek293": [],
        "cloning": [],
        "dna": [],
        "task": [],
        "assay": [],
        "other": [],
    }
    assert split_projects_list_by_activities(
        projects_lists.get("proje asldkfjaldskjf")
    ) == {
        "sf9": [],
        "hek293": [],
        "cloning": [],
        "dna": [],
        "task": [],
        "assay": [],
        "other": [],
    }
    
    d = split_projects_list_by_activities(
        projects_lists.get("project_list_all_dna")
    ).get("dna")
    assert d is not None
    assert len(d) == 3

    norm = split_projects_list_by_activities(
        projects_lists.get("project_list_normal")
    )
    sf9 = norm.get("sf9")
    assert sf9 is not None
    assert len(sf9) == 1
    hek293 = norm.get("hek293")
    assert hek293 is not None
    assert len(hek293) == 2
    assay = norm.get("assay")
    assert assay is not None
    assert len(assay) == 2
    assay_project_2 = assay[1]
    assert assay_project_2 is not None 
    assert assay_project_2.get("projectname") == "assay project 2"


@pytest.fixture
def no_requests(monkeypatch):
    """Remove requests.sessions.Session.request for all tests."""
    monkeypatch.delattr("requests.sessions.Session.request")


# test all the endpoints
# test all the helper functions
