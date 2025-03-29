from fastapi.testclient import TestClient
from ..main import app
import pytest
from datetime import datetime
import uuid
from .test_query_logs import test_user_token  # reuse auth fixture
from app.config.database import get_supabase_client

client = TestClient(app)

@pytest.fixture
def setup_test_chunks(test_user_token):
    """Create test documents and chunks"""
    supabase = get_supabase_client(use_service_role=True)
    doc_id = str(uuid.uuid4())
    
    # Get company_id from token payload
    from ..auth.jwt_handler import verify_token
    user_data = verify_token(test_user_token)
    company_id = user_data['company_id']
    
    print(f"Setting up test data for company_id: {company_id}")  # Debug print
    
    # Create test document
    document_data = {
        "id": doc_id,
        "company_id": company_id,
        "file_name": "test.pdf",
        "file_type": "pdf",
        "file_path": f"/test/{doc_id}.pdf",
        "status": "processed",
        "uploaded_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "metadata": {},
        "chunk_count": 2
    }
    
    # Create test chunks (removed company_id field)
    chunk_data = [
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "chunk_index": 0,
            "content": "This is a test chunk containing specific test query content.",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "vector_status": "pending"
        },
        {
            "id": str(uuid.uuid4()),
            "document_id": doc_id,
            "chunk_index": 1,
            "content": "This is another chunk with different content.",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "vector_status": "pending"
        }
    ]
    
    try:
        # Insert test data
        doc_response = supabase.table('documents').insert(document_data).execute()
        print(f"Inserted document: {doc_response.data}")  # Debug print
        
        chunks_response = supabase.table('document_chunks').insert(chunk_data).execute()
        print(f"Inserted chunks: {chunks_response.data}")  # Debug print
        
        # Verify data was inserted
        verify_doc = supabase.table('documents').select("*").eq('id', doc_id).execute()
        verify_chunks = supabase.table('document_chunks').select("*").eq('document_id', doc_id).execute()
        print(f"Verification - Document exists: {bool(verify_doc.data)}, Chunks exist: {bool(verify_chunks.data)}")
        
        return doc_id  # Changed from yield to return since we're not async
        
    except Exception as e:
        print(f"Error in setup_test_chunks: {e}")
        raise
    finally:
        # Move cleanup to a separate teardown fixture
        pass

@pytest.fixture(autouse=True)
def cleanup_test_chunks(test_user_token, setup_test_chunks):
    """Cleanup test data after test"""
    yield
    supabase = get_supabase_client(use_service_role=True)
    doc_id = setup_test_chunks
    try:
        supabase.table('document_chunks').delete().eq('document_id', doc_id).execute()
        supabase.table('documents').delete().eq('id', doc_id).execute()
        print(f"Cleaned up test data for doc_id: {doc_id}")
    except Exception as e:
        print(f"Error in cleanup: {e}")

def test_rag_query(test_user_token, setup_test_chunks):
    """Test RAG query endpoint"""
    query_data = {
        "query": "specific test query",  # This matches our test chunk content
        "max_results": 3
    }
    
    response = client.post(
        "/rag/query",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json=query_data
    )
    
    print(f"Response status: {response.status_code}")  # Debug print
    print(f"Response body: {response.text}")  # Debug print
    
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == query_data["query"]
    assert isinstance(data["relevant_chunks"], list)
    assert len(data["relevant_chunks"]) > 0  # Should find at least one chunk
    assert "metadata" in data

def test_unauthorized_rag_query():
    """Test RAG query without authorization"""
    response = client.post("/rag/query", json={"query": "test"})
    assert response.status_code == 403