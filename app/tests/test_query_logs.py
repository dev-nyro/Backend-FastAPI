from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime
from uuid import uuid4
from app.config.database import get_supabase_client
from passlib.context import CryptContext  # Add this import

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Create password context

class TestData:
    log_id = None
    user_id = None
    user_token = None

@pytest.fixture
def test_user_token(setup_company):
    """Create a test user and return their token"""
    supabase = get_supabase_client(use_service_role=True)
    
    # Create test user
    email = f"test_logs_{uuid4()}@example.com"
    password = "testpass123"
    
    user_data = {
        "email": email,
        "full_name": "Test Logs User",
        "role": "user",
        "hashed_password": pwd_context.hash(password),  # Hash the password properly
        "company_id": setup_company,
        "created_at": datetime.utcnow().isoformat(),
        "is_active": True
    }
    
    try:
        # Create user
        user_response = supabase.table('users').insert(user_data).execute()
        TestData.user_id = user_response.data[0]['id']
        
        # Get token
        login_response = client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed with response: {login_response.text}")  # Debug print
            raise Exception(f"Login failed: {login_response.json()}")
            
        token = login_response.json()["access_token"]
        TestData.user_token = token
        return token
        
    except Exception as e:
        print(f"Error setting up test user: {e}")
        raise

@pytest.fixture
def test_query_log_data():
    """Create test query log data"""
    return {
        "query": "Test query",
        "response": "Test response",
        "relevance_score": 0.95,
        "metadata": {
            "processing_time": 0.5,
            "document_ids": ["doc1", "doc2"]
        }
    }

@pytest.mark.order(1)
def test_create_query_log(test_user_token, test_query_log_data):
    """Test creating a new query log"""
    print(f"\nUsing token: {test_user_token[:20]}...")  # Debug print
    
    response = client.post(
        "/query-logs/",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json=test_query_log_data
    )
    
    print(f"Response status: {response.status_code}")  # Debug print
    print(f"Response body: {response.text}")  # Debug print
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["query"] == test_query_log_data["query"]
    assert data["response"] == test_query_log_data["response"]
    
    TestData.log_id = data["id"]

@pytest.mark.order(2)
def test_get_query_logs(test_user_token):
    """Test getting query logs"""
    print(f"\nUsing token: {test_user_token[:20]}...")  # Debug print
    
    response = client.get(
        "/query-logs/",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")  # Debug print
    print(f"Response body: {response.text}")  # Debug print
    
    assert response.status_code == 200
    logs = response.json()
    assert isinstance(logs, list)

@pytest.mark.order(3)
def test_get_specific_query_log(test_user_token):
    """Test getting a specific query log"""
    assert TestData.log_id is not None, "No log_id available"
    print(f"\nGetting log with ID: {TestData.log_id}")  # Debug print
    
    response = client.get(
        f"/query-logs/{TestData.log_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    
    print(f"Response status: {response.status_code}")  # Debug print
    print(f"Response body: {response.text}")  # Debug print
    
    assert response.status_code == 200
    log = response.json()
    assert log["id"] == TestData.log_id

def test_unauthorized_access():
    """Test accessing logs without authorization"""
    response = client.get("/query-logs/")
    assert response.status_code == 403

def test_invalid_log_id(test_user_token):
    """Test accessing non-existent log"""
    fake_id = str(uuid4())
    response = client.get(
        f"/query-logs/{fake_id}",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )
    assert response.status_code == 404