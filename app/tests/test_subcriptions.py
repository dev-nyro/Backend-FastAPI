from fastapi.testclient import TestClient
from app.main import app
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

client = TestClient(app)

# Store test data at module level
class TestData:
    subscription_id = None

@pytest.fixture
def test_subscription_data(setup_company):
    """Create test subscription data with all required fields"""
    current_time = datetime.utcnow()
    end_time = current_time + timedelta(days=365)
    
    return {
        "company_id": str(setup_company),  # Convert UUID to string
        "plan_type": "pro",
        "max_documents": 1000,
        "max_queries": 5000,
        "start_date": current_time.isoformat(),
        "end_date": end_time.isoformat()
    }

def test_create_subscription(admin_token, test_subscription_data):
    """Test creating a new subscription"""
    print(f"\nCreating subscription with data: {test_subscription_data}")  # Debug print
    response = client.post(
        "/subscriptions/",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=test_subscription_data
    )
    
    # Debug prints
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    
    # Store the ID for subsequent tests
    TestData.subscription_id = data["id"]

def test_get_subscriptions(admin_token):
    """Test getting all subscriptions"""
    response = client.get(
        "/subscriptions/",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    subscriptions = response.json()
    assert isinstance(subscriptions, list)
    assert len(subscriptions) > 0

def test_get_specific_subscription(admin_token):
    """Test getting a specific subscription"""
    assert TestData.subscription_id is not None, "No subscription ID available"
    response = client.get(
        f"/subscriptions/{TestData.subscription_id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Debug prints
    print(f"Getting subscription with ID: {TestData.subscription_id}")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200

def test_update_subscription(admin_token):
    """Test updating a subscription"""
    assert TestData.subscription_id is not None, "No subscription ID available"
    update_data = {
        "plan_type": "enterprise",
        "max_documents": 2000,
        "max_queries": 10000
    }
    
    response = client.put(
        f"/subscriptions/{TestData.subscription_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json=update_data
    )
    
    # Debug prints
    print(f"Updating subscription with ID: {TestData.subscription_id}")
    print(f"Update data: {update_data}")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200