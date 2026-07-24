from typing import List
from app.schemas.test_schema import IntegrationTestRequest, TestCasePayload

def generate_test_suite(request: IntegrationTestRequest) -> List[TestCasePayload]:
    """
    Micro-Agent 1: Test Suite Generator (Pure Python Deterministic)
    Generates 3 test payload variations (Positive, Edge/Boundary, Negative) based on target endpoint & scenario.
    """
    target = request.target_endpoint.lower()
    desc = request.scenario_description.lower()

    # Determine domain context for intelligent payload generation
    if "generate" in target or "execute" in target or "integration" in target or "test" in target:
        positive_data = {
            "target_endpoint": "https://jsonplaceholder.typicode.com/posts",
            "scenario_description": "Uji integrasi membuat postingan baru"
        }
        edge_data = {
            "target_endpoint": "https://jsonplaceholder.typicode.com/posts",
            "scenario_description": "Skenario teks deskripsi batas maksimum buffer data " * 10
        }
        negative_data = {
            "target_endpoint": "not_a_valid_url_address",
            "scenario_description": ""
        }
    elif "user" in target or "auth" in target:
        positive_data = {"username": "testuser_qa", "email": "qa_integration@example.com", "role": "developer"}
        edge_data = {"username": "u" * 150, "email": "edge_case_long_string_email@subdomain.testing.org", "role": "admin"}
        negative_data = {"username": "", "email": "not-an-email-address", "role": None}
    elif "product" in target or "item" in target or "shop" in target:
        positive_data = {"title": "Barang Uji Integrasi", "price": 45000, "category": "Elektronik", "stock": 10}
        edge_data = {"title": "A" * 255, "price": 0, "category": "General", "stock": 999999}
        negative_data = {"title": None, "price": -500, "category": 12345}
    else:
        # Default payload pattern (e.g. JSONPlaceholder / General Microservice API)
        positive_data = {
            "title": "Skenario Uji Integrasi Valid",
            "body": f"Eksekusi skenario uji otomatis: {request.scenario_description}",
            "userId": 1,
            "status": "active"
        }
        edge_data = {
            "title": "E" * 200,
            "body": "Payload batas maksimum buffer teks...",
            "userId": 999999,
            "status": "edge_case"
        }
        negative_data = {
            "title": None,
            "body": "",
            "userId": "invalid_integer_id",
            "status": "INVALID_STATUS_ENUM"
        }

    return [
        TestCasePayload(
            case_type="Positif (Valid Payload)",
            payload_data=positive_data,
            expected_behavior="HTTP 200 OK / 201 Created — Endpoint merespons dengan sukses & struktur data valid."
        ),
        TestCasePayload(
            case_type="Edge Case (Boundary Input)",
            payload_data=edge_data,
            expected_behavior="HTTP 200 OK / 422 Unprocessable Entity — Endpoint menangani batas maksimum data dengan aman tanpa 500 Server Error."
        ),
        TestCasePayload(
            case_type="Negatif (Invalid Payload)",
            payload_data=negative_data,
            expected_behavior="HTTP 200 OK / 400 Bad Request / 422 Validation Error — Endpoint merespons tanpa mengalami 500 Internal Server Error."
        )
    ]
