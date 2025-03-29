import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config.database import get_supabase_client
from datetime import datetime, timedelta
from uuid import uuid4
import pytz
from functools import lru_cache
from supabase import create_client
import httpx
from app.config import settings
from passlib.context import CryptContext

client = TestClient(app)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")  # Create at module level

@pytest.fixture(autouse=True, scope="session")
def cleanup_test_data():
    """Clean up all test data before and after tests"""
    supabase = get_cached_supabase()
    
    def delete_all_test_data():
        """Clean up all test data before and after tests"""
        try:
            print("Starting database cleanup...")
            supabase = get_cached_supabase()
            
            # Delete in correct order to respect foreign key constraints
            
            # First delete query logs
            print("Deleting query logs...")
            supabase.table('query_logs')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            # Then delete document chunks
            print("Deleting document chunks...")
            supabase.table('document_chunks')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            # Then delete documents
            print("Deleting documents...")
            supabase.table('documents')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            # Delete subscriptions
            print("Deleting subscriptions...")
            supabase.table('subscriptions')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            # Delete users
            print("Deleting users...")
            supabase.table('users')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            # Finally delete companies
            print("Deleting companies...")
            supabase.table('companies')\
                .delete()\
                .gte('id', '00000000-0000-0000-0000-000000000000')\
                .execute()
            
            print("Successfully cleaned up test data")
        except Exception as e:
            print(f"Error cleaning up test data: {e}")
            raise
    
    # Clean up before tests
    delete_all_test_data()
    
    yield  # Run tests
    
    # Clean up after tests
    delete_all_test_data()

def get_cached_supabase():
    """Get Supabase client with service role"""
    try:
        # Create client without options
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
        
        return client
        
    except Exception as e:
        print(f"Error initializing Supabase client: {e}")
        raise

def get_test_company():
    """Get or create test company"""
    supabase = get_cached_supabase()
    company_data = {
        "name": f"Test Company {uuid4()}",
        "email": f"company_{uuid4()}@test.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    response = supabase.table('companies').insert(company_data).execute()
    return response.data[0]['id']

@pytest.fixture(scope="session")
def setup_company():
    """Create a test company"""
    supabase = get_cached_supabase()
    company_data = {
        "name": f"Test Company {uuid4()}",
        "email": f"company_{uuid4()}@test.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    try:
        response = supabase.table('companies')\
            .insert(company_data)\
            .execute()
        print(f"Created test company: {response.data[0]['id']}")
        return response.data[0]['id']
    except Exception as e:
        print(f"Error creating test company: {e}")
        raise

@pytest.fixture(scope="session", autouse=True)
def setup_subscription(setup_company):
    """Create a test subscription for the company"""
    supabase = get_cached_supabase()
    
    subscription_data = {
        "company_id": setup_company,
        "plan_type": "pro",
        "start_date": datetime.now(pytz.UTC).isoformat(),
        "end_date": (datetime.now(pytz.UTC) + timedelta(days=30)).isoformat(),
        "max_documents": 1000,
        "max_queries": 5000
    }
    
    try:
        # Delete any existing subscriptions
        existing = supabase.table('subscriptions')\
            .select("*")\
            .eq('company_id', setup_company)\
            .execute()
            
        if existing.data:
            supabase.table('subscriptions')\
                .delete()\
                .eq('company_id', setup_company)\
                .execute()
        
        # Create new subscription
        response = supabase.table('subscriptions')\
            .insert(subscription_data)\
            .execute()
            
        if not response.data:
            raise Exception("Failed to create subscription")
            
        return response.data[0]['id']
        
    except Exception as e:
        print(f"Error setting up subscription: {e}")
        raise

@pytest.fixture(scope="session")
def admin_token(setup_company):
    """Create an admin user and get token"""
    supabase = get_cached_supabase()
    
    # Test credentials
    admin_email = "admin@test.com"
    admin_password = "adminpass123"
    
    try:
        # Clean up existing user if exists
        print(f"Cleaning up existing admin user: {admin_email}")
        supabase.table('users').delete().eq('email', admin_email).execute()
        
        # Create new admin user with properly hashed password
        hashed_password = pwd_context.hash(admin_password)
        
        admin_data = {
            "email": admin_email,
            "hashed_password": hashed_password,  # Use the hashed password
            "full_name": "Test Admin",
            "role": "admin",
            "company_id": setup_company,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        print(f"Creating admin user: {admin_email}")
        response = supabase.table('users').insert(admin_data).execute()
        
        if not response.data:
            raise Exception("Failed to create admin user")
            
        print(f"Admin user created successfully")
        
        # Now get the token by making a login request
        login_response = client.post(
            "/auth/login",
            data={
                "username": admin_email,
                "password": admin_password
            }
        )
        
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.json()}")
            raise Exception("Failed to get admin token")
            
        return login_response.json()["access_token"]
        
    except Exception as e:
        print(f"Error in admin_token fixture: {str(e)}")
        raise
