from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.config.database import get_supabase_client
from datetime import datetime
from uuid import uuid4
import os

client = TestClient(app)

class TestData:
    """Class to store test data between tests"""
    user_id = None
    email = None
    password = None

@pytest.fixture(scope="session")
def setup_company():
    """Create a test company first"""
    supabase = get_supabase_client(use_service_role=True)  # Use service role directly
    company_data = {
        "name": "Test Company",
        "email": "company@test.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    try:
        # First check if company exists using service role
        existing = supabase.table('companies').select("*").eq('email', company_data['email']).execute()
        if existing.data:
            return existing.data[0]['id']
        
        # Create new company with service role client
        response = supabase.table('companies').insert(company_data).execute()
        print(f"Company created: {response.data}")  # Debug info
        return response.data[0]['id']
    except Exception as e:
        print(f"Error creating company: {e}")
        raise

@pytest.fixture(scope="session")
def test_user(setup_company):
    """Create test user with proper schema"""
    supabase = get_supabase_client(use_service_role=True)
    email = f"test_{uuid4()}@example.com"
    password = "testpassword123"
    
    user_data = {
        "email": email,
        "full_name": "Test User",
        "role": "user",
        "hashed_password": password,  # In real app this would be hashed
        "company_id": setup_company,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    try:
        response = supabase.table('users')\
            .insert(user_data)\
            .execute()
            
        print(f"Created test user: {response.data[0]['id']}")
        print(f"Test user email: {email}")  # Debug print
        print(f"Test user password: {password}")  # Debug print
        
        # Store credentials for use in tests
        TestData.user_id = response.data[0]['id']
        TestData.email = email
        TestData.password = password
        
        return response.data[0]['id']
    except Exception as e:
        print(f"Error creating test user: {e}")
        raise

@pytest.fixture
def auth_token(test_user):
    """Get auth token using stored credentials"""
    response = client.post(
        "/auth/login",
        data={
            "username": TestData.email,  # Use stored email
            "password": TestData.password  # Use stored password
        }
    )
    if response.status_code != 200:
        print(f"Auth token response: {response.json()}")
        print(f"Using email: {TestData.email}")
        print(f"Using password: {TestData.password}")
        raise Exception("Failed to get auth token")
    return response.json()["access_token"]

def test_register_user(setup_company):
    test_email = f"test_{uuid4()}@example.com"
    
    # Print the company_id for debugging
    print(f"Using company_id: {setup_company}")
    
    user_data = {
        "email": test_email,
        "password": "testpassword",
        "full_name": "New Test User",
        "role": "user",
        "company_id": setup_company  # Added required company_id
    }
    
    response = client.post("/auth/register", json=user_data)
    if response.status_code != 200:
        print(f"Register response: {response.json()}")  # Debug info
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "user" in response.json()
    user = response.json()["user"]
    assert user["full_name"] == user_data["full_name"]
    assert user["email"] == user_data["email"]
    assert user["role"] == user_data["role"]
    assert "is_active" in user
    assert "created_at" in user

def test_login_success(test_user):
    """Test successful login with correct credentials"""
    print(f"Attempting login with email: {TestData.email}")  # Debug print
    response = client.post(
        "/auth/login",
        data={
            "username": TestData.email,  # Use stored email
            "password": TestData.password  # Use stored password
        }
    )
    
    if response.status_code != 200:
        print(f"Login response: {response.json()}")  # Debug info
        print(f"Using email: {TestData.email}")
        print(f"Using password: {TestData.password}")
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert "user" in response.json()

def test_login_invalid_credentials():
    response = client.post(
        "/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401

def test_protected_route_without_token():
    response = client.get("/users/1")
    assert response.status_code == 403
    assert "detail" in response.json()

def test_protected_route_with_token(auth_token, test_user):
    url = f"/users/{TestData.user_id}"  # Use the stored user ID
    print(f"\nTesting URL: {url}")
    print(f"Using auth token: {auth_token[:20]}...")
    print(f"Using stored user ID: {TestData.user_id}")
    
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    if response.status_code != 200:
        print(f"Response: {response.json()}")
        print(f"Full URL: {url}")
        print(f"User ID being tested: {TestData.user_id}")
    
    assert response.status_code == 200
    assert "data" in response.json()
    assert response.json()["data"]["id"] == TestData.user_id

def test_auth_me_endpoint(auth_token):
    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
    assert "user" in response.json()
    assert response.json()["user"]["sub"] == TestData.email

def test_invalid_token():
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 403
    assert "detail" in response.json()