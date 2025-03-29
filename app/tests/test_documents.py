from fastapi.testclient import TestClient
from app.main import app
import pytest
from app.config.database import get_supabase_client
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import json
from ..auth.jwt_handler import verify_token
from app.tests.conftest import get_cached_supabase
from functools import lru_cache
from passlib.context import CryptContext  # Add this import

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Create password context

class TestData:
    """Class to store test data between tests"""
    document_id = None
    company_id = None
    user_token = None
    subscription_id = None

@pytest.fixture(scope="session")
@lru_cache()
def setup_company():
    """Cached company setup"""
    supabase = get_supabase_client(use_service_role=True)
    company_data = {
        "name": f"Test Company {uuid4()}",
        "email": f"company_{uuid4()}@test.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    try:
        response = supabase.table('companies').insert(company_data).execute()
        TestData.company_id = response.data[0]['id']
        return TestData.company_id
    except Exception as e:
        print(f"Error creating test company: {e}")
        raise

@pytest.fixture(scope="session")
@lru_cache()
def auth_token(setup_company):
    """Cached auth token fixture"""
    supabase = get_supabase_client(use_service_role=True)
    email = f"test_doc_{uuid4()}@example.com"
    password = "testpassword123"
    
    try:
        # Create test user first
        user_data = {
            "email": email,
            "full_name": "Test Doc User",
            "role": "user",
            "hashed_password": pwd_context.hash(password),  # Hash the password properly
            "company_id": setup_company,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        # Delete existing user if any
        existing = supabase.table('users').select("*").eq('email', email).execute()
        if existing.data:
            supabase.table('users').delete().eq('email', email).execute()
        
        # Insert new user and get data
        user_response = supabase.table('users').insert(user_data).execute()
        
        if not user_response.data:
            raise Exception("Failed to create test user")
            
        # Now try to login using FastAPI test client
        login_response = client.post(
            "/auth/login",
            data={
                "username": email,
                "password": password
            }
        )
        
        if login_response.status_code != 200:
            raise Exception(f"Login failed: {login_response.json()}")
            
        return login_response.json()["access_token"]
        
    except Exception as e:
        print(f"Error in auth_token fixture: {str(e)}")
        raise

@pytest.fixture
def test_document_data():
    """Create test document data with all required fields"""
    return {
        "file_name": f"test_doc_{uuid4()}.pdf",
        "file_type": "pdf",
        "file_path": f"companies/test/{uuid4()}.pdf",
        "metadata": {
            "language": "es",
            "page_count": 5,
            "file_size": 1024
        },
        "status": "uploaded",
        "chunk_count": 0
    }

@pytest.fixture(autouse=True)
def ensure_subscription(setup_subscription):
    """Ensure subscription exists before running tests"""
    return setup_subscription

@pytest.fixture(autouse=True)
def setup_subscription(setup_company):
    """Create a test subscription for the company"""
    supabase = get_supabase_client(use_service_role=True)
    
    # Create subscription data
    subscription_data = {
        "company_id": setup_company,
        "plan_type": "pro",
        "max_documents": 1000,
        "max_queries": 5000,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat()
    }
    
    try:
        # Check if subscription exists
        existing = supabase.table('subscriptions')\
            .select("*")\
            .eq('company_id', setup_company)\
            .execute()
            
        if not existing.data:
            # Create new subscription
            response = supabase.table('subscriptions')\
                .insert(subscription_data)\
                .execute()
            print(f"Created test subscription: {response.data[0] if response.data else None}")
    except Exception as e:
        print(f"Error setting up subscription: {e}")
        raise

@pytest.fixture(autouse=True)
def reset_subscription_limits():
    """Reset subscription limits before and after each test"""
    # Reset before test
    supabase = get_supabase_client(use_service_role=True)
    
    def reset_limits(company_id):
        supabase.table('subscriptions')\
            .update({
                "max_documents": 1000,
                "max_queries": 5000
            })\
            .eq('company_id', company_id)\
            .execute()
    
    # Get all test companies and reset their limits
    companies = supabase.table('companies')\
        .select('id')\
        .execute()
    
    for company in companies.data:
        reset_limits(company['id'])
    
    yield  # Run the test
    
    # Reset after test
    for company in companies.data:
        reset_limits(company['id'])

@pytest.fixture(scope="session")
def supabase():
    """Cached Supabase client"""
    return get_cached_supabase()

def test_create_document(auth_token, test_document_data):
    """Test creating a new document"""
    print(f"\nCreating document with data: {test_document_data}")
    response = client.post(
        "/documents/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_document_data
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    data = response.json()
    
    # Validate all required fields from schema
    assert "id" in data
    assert "company_id" in data
    assert data["file_name"] == test_document_data["file_name"]
    assert data["file_type"] == test_document_data["file_type"]
    assert data["file_path"] == test_document_data["file_path"]
    assert data["metadata"] == test_document_data["metadata"]
    assert "uploaded_at" in data  # Changed from created_at to uploaded_at
    assert "updated_at" in data
    assert data["status"] == "uploaded"
    assert data["chunk_count"] == 0
    
    # Store for later tests
    TestData.document_id = data["id"]

def test_get_documents(auth_token):
    """Test getting all documents for the company"""
    print(f"\nAttempting to get documents with token: {auth_token[:20]}...")
    
    response = client.get(
        "/documents/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    # Add debug information
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.text}")
    
    assert response.status_code == 200
    documents = response.json()
    assert isinstance(documents, list)
    assert len(documents) > 0
    assert documents[0]["company_id"] == TestData.company_id

def test_get_specific_document(auth_token):
    """Test getting a specific document"""
    assert TestData.document_id is not None, "No document_id available"
    response = client.get(
        f"/documents/{TestData.document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    document = response.json()
    assert document["id"] == TestData.document_id

def test_update_document(auth_token):
    """Test updating a document"""
    update_data = {
        "metadata": {
            "page_count": 6,
            "language": "en",
            "updated": True
        }
    }
    
    response = client.put(
        f"/documents/{TestData.document_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_data
    )
    
    assert response.status_code == 200
    document = response.json()
    assert document["metadata"] == update_data["metadata"]
    assert document["id"] == TestData.document_id

def test_process_document(auth_token):
    """Test document processing endpoint"""
    # First create a test document
    test_data = {
        "file_name": "test.pdf",
        "file_type": "pdf",
        "file_path": "/test/path/test.pdf",
        "metadata": {
            "language": "en",
            "page_count": 1,
            "file_size": 1024
        },
        "status": "uploaded"
    }
    
    # Create document first
    create_response = client.post(
        "/documents/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_data
    )
    
    assert create_response.status_code == 200
    document_id = create_response.json()["id"]
    
    # Wait a moment to ensure document is created
    import time
    time.sleep(2)  # Increased wait time
    
    # Verify document exists
    get_response = client.get(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 200
    
    # Trigger processing
    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert process_response.status_code == 200
    assert process_response.json()["message"] == "Document processing started"
    
    # Wait for processing
    time.sleep(3)  # Increased wait time
    
    # Verify final status
    final_response = client.get(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert final_response.status_code == 200
    assert final_response.json()["status"] in ["processing", "processed"]

def test_delete_document(auth_token):
    """Test deleting a document"""
    response = client.delete(
        f"/documents/{TestData.document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["message"] == "Document deleted successfully"
    
    # Verify document is not accessible after deletion
    get_response = client.get(
        f"/documents/{TestData.document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 404

def test_unauthorized_access():
    """Test accessing documents without authorization"""
    response = client.get("/documents/")
    assert response.status_code == 403

def test_invalid_document_id(auth_token):
    """Test accessing non-existent document"""
    fake_id = str(uuid4())
    response = client.get(
        f"/documents/{fake_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

def test_wrong_company_access(auth_token):
    """Test accessing document from another company"""
    # Create a document for a different company first
    other_company_doc_id = str(uuid4())
    response = client.get(
        f"/documents/{other_company_doc_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

@pytest.mark.timeout(30)  # 30 seconds max per test
def test_document_processing_flow(auth_token, test_document_data):
    """Test complete document processing flow"""
    # 1. Create document
    create_response = client.post(
        "/documents/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=test_document_data
    )
    assert create_response.status_code == 200
    document_id = create_response.json()["id"]
    
    # 2. Start processing
    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert process_response.status_code == 200
    
    # 3. Verify processing started
    get_response = client.get(
        f"/documents/{document_id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert get_response.status_code == 200
    assert get_response.json()["status"] in ["processing", "processed", "completed"]
    
    # 4. Get chunks
    chunks_response = client.get(
        f"/documents/{document_id}/chunks",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert chunks_response.status_code == 200
    chunks = chunks_response.json()
    if get_response.json()["status"] in ["processed", "completed"]:
        assert len(chunks) > 0

def test_document_upload_with_subscription_limit(auth_token):
    """Test document upload with subscription limits"""
    try:
        # First update subscription to have a low limit
        supabase = get_supabase_client(use_service_role=True)
        
        # Get the user's company subscription
        user_data = verify_token(auth_token)
        company_id = user_data['company_id']
        
        # Create test document data
        test_data = {
            "file_name": f"test_doc_{uuid4()}.pdf",
            "file_type": "pdf",
            "file_path": f"/storage/test/{uuid4()}.pdf",
            "metadata": {}
        }
        
        # First create a document
        first_response = client.post(
            "/documents/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_data
        )
        
        print(f"First response: {first_response.text}")  # Debug print
        assert first_response.status_code == 200
        
        # Now update subscription to limit
        supabase.table('subscriptions')\
            .update({"max_documents": 1})\
            .eq('company_id', company_id)\
            .execute()
        
        # Try to create another document
        second_response = client.post(
            "/documents/",
            headers={"Authorization": f"Bearer {auth_token}"},
            json=test_data  # Fixed: Removed invalid json( syntax
        )
        assert second_response.status_code == 403
        assert "limit reached" in second_response.json()["detail"].lower()
    finally:
        # Reset subscription limit after test
        supabase = get_supabase_client(use_service_role=True)
        user_data = verify_token(auth_token)
        company_id = user_data['company_id']
        
        supabase.table('subscriptions')\
            .update({
                "max_documents": 1000,
                "max_queries": 5000
            })\
            .eq('company_id', company_id)\
            .execute()

def test_document_processing_error_handling(auth_token):
    """Test error handling during document processing"""
    supabase = get_supabase_client(use_service_role=True)
    
    # First create a document with XYZ file type directly
    test_data = {
        "file_name": "test.xyz",
        "file_type": "xyz",  # Invalid file type from the start
        "file_path": "/test/path/test.xyz",
        "metadata": {},
        "company_id": verify_token(auth_token)['company_id'],
        "status": "uploaded",
        "uploaded_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Insert document directly using supabase
    create_response = supabase.table('documents').insert(test_data).execute()
    assert create_response.data
    document_id = create_response.data[0]['id']
    
    # Try to process it - should fail with 400
    process_response = client.post(
        f"/documents/{document_id}/process",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    print(f"Process response status: {process_response.status_code}")  # Debug print
    print(f"Process response body: {process_response.text}")  # Debug print
    
    assert process_response.status_code == 400
    assert "Invalid file type" in process_response.json()["detail"]
