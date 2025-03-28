from fastapi.testclient import TestClient
from app.main import app
import pytest
from uuid import uuid4

client = TestClient(app)

@pytest.fixture
def test_company_data():
    return {
        "name": f"Test Company {uuid4()}",
        "email": f"company_{uuid4()}@test.com"
    }

@pytest.fixture
def test_company(setup_company):
    """Return the test company ID"""
    return setup_company

def test_get_companies_list(admin_token):
    """Test getting list of companies"""
    response = client.get(
        "/companies/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    companies = response.json()
    assert isinstance(companies, list)
    if len(companies) > 0:
        assert "id" in companies[0]
        assert "name" in companies[0]
        assert "email" in companies[0]

def test_get_company_by_id(admin_token, test_company):
    """Test getting a specific company by ID"""
    response = client.get(
        f"/companies/{test_company}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    company = response.json()
    assert company["id"] == str(test_company)
    assert "name" in company
    assert "email" in company

def test_create_company(admin_token, test_company_data):
    """Test creating a new company"""
    response = client.post(
        "/companies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=test_company_data
    )
    
    assert response.status_code == 200
    created_company = response.json()
    assert created_company["name"] == test_company_data["name"]
    assert created_company["email"] == test_company_data["email"]
    assert "id" in created_company

def test_update_company(admin_token, test_company):
    """Test updating an existing company"""
    update_data = {
        "name": f"Updated Company {uuid4()}"
    }
    
    response = client.put(
        f"/companies/{test_company}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    updated_company = response.json()
    assert updated_company["name"] == update_data["name"]
    assert updated_company["id"] == str(test_company)

def test_delete_company(admin_token, test_company_data):
    """Test deleting (soft-delete) a company"""
    # First create a company to delete
    create_response = client.post(
        "/companies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=test_company_data
    )
    company_id = create_response.json()["id"]
    
    # Then delete it
    delete_response = client.delete(
        f"/companies/{company_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert delete_response.status_code == 200
    assert "message" in delete_response.json()
    
    # Verify it's soft-deleted
    get_response = client.get(
        f"/companies/{company_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == 200
    assert not get_response.json()["is_active"]

def test_unauthorized_access():
    """Test accessing endpoints without authorization"""
    response = client.get("/companies/")
    assert response.status_code == 403
    
    response = client.post("/companies/", json={"name": "Test", "email": "test@test.com"})
    assert response.status_code == 403

def test_invalid_company_id(admin_token):
    """Test accessing non-existent company"""
    fake_id = str(uuid4())
    response = client.get(
        f"/companies/{fake_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404

def test_duplicate_company_email(admin_token, test_company_data):
    """Test creating company with duplicate email"""
    # Create first company
    response = client.post(
        "/companies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=test_company_data
    )
    assert response.status_code == 200
    
    # Try to create second company with same email
    response = client.post(
        "/companies/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=test_company_data
    )
    assert response.status_code == 400