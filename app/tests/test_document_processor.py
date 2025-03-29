import pytest
from ..utils.document_processor import DocumentProcessor
import io
from PyPDF2 import PdfWriter
from datetime import datetime
import uuid
from app.config.database import get_supabase_client
from typing import Dict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

@pytest.fixture(scope="module")
def test_company():
    """Create a test company and ensure it exists throughout the tests"""
    supabase = get_supabase_client(use_service_role=True)
    company_id = str(uuid.uuid4())  # Generate company_id first
    
    company_data = {
        "id": company_id,
        "name": f"Test Company {company_id}",
        "email": f"company_{company_id}@test.com",
        "is_active": True,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Create company
    response = supabase.table('companies').insert(company_data).execute()
    assert response.data, "Failed to create test company"
    
    yield company_id
    
    # Cleanup after tests - delete in correct order
    try:
        # First delete document chunks
        supabase.table('document_chunks')\
            .delete()\
            .eq('document_id', company_id)\
            .execute()
            
        # Then delete documents
        supabase.table('documents')\
            .delete()\
            .eq('company_id', company_id)\
            .execute()
            
        # Finally delete company
        supabase.table('companies')\
            .delete()\
            .eq('id', company_id)\
            .execute()
    except Exception as e:
        print(f"Error in company cleanup: {str(e)}")

@pytest.fixture
def sample_pdf_content():
    """Create a sample PDF for testing with actual text content"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    
    # Add multiple lines of text
    text = "This is a sample document for testing. " * 20
    y_position = 750  # Start from top of page
    for line in range(10):
        c.drawString(50, y_position, text)
        y_position -= 40
    
    c.save()
    return buffer.getvalue()

@pytest.fixture
def test_processor():
    return DocumentProcessor()

def test_create_chunks(test_processor):
    """Test text chunking functionality"""
    text = "This is sentence one. This is sentence two. " * 50
    chunks = test_processor.create_chunks(text, chunk_size=100)
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)

@pytest.mark.asyncio
async def test_process_document(test_processor, sample_pdf_content, test_company):
    """Test document processing with a sample PDF"""
    doc_id = str(uuid.uuid4())
    file_path = f"test/{doc_id}.pdf"
    
    # First upload the sample PDF to storage
    supabase = get_supabase_client(use_service_role=True)
    try:
        print(f"\nStarting document processing test with ID: {doc_id}")
        
        # Create the bucket if it doesn't exist
        try:
            supabase.storage.create_bucket('documents')
            print("Created documents bucket")
        except Exception as e:
            if "'statusCode': 409" not in str(e):  # Ignore "already exists" error
                raise e
            print("Documents bucket already exists")
        
        # Upload sample PDF to storage
        supabase.storage.from_('documents').upload(
            file_path,
            sample_pdf_content,
            {"content-type": "application/pdf"}
        )
        print("Uploaded PDF to storage")
        
        # Create document record
        document_data = {
            "id": doc_id,
            "file_path": file_path,
            "file_type": "pdf",
            "file_name": "test.pdf",
            "status": "pending",
            "company_id": test_company,
            "uploaded_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {},
            "chunk_count": 0
        }
        
        # Insert test document
        response = test_processor.supabase.table('documents')\
            .insert(document_data)\
            .execute()
        assert response.data, "Failed to create test document"
        print("Created document record in database")
        
        # Process document
        print("Starting document processing...")
        result = await test_processor.process_document(doc_id)
        assert result["status"] == "success"
        print("Document processing completed")
        
        # Add a longer delay to ensure processing is complete
        import asyncio
        await asyncio.sleep(5)
        
        # Verify document was processed
        doc_response = test_processor.supabase.table('documents')\
            .select('*')\
            .eq('id', doc_id)\
            .single()\
            .execute()
        assert doc_response.data["status"] == "processed", "Document not properly processed"
        
        # Verify chunks were created
        chunks_response = test_processor.supabase.table('document_chunks')\
            .select('*')\
            .eq('document_id', doc_id)\
            .execute()
        
        print(f"Found {len(chunks_response.data)} chunks")
        assert len(chunks_response.data) > 0, "No chunks were created"
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        raise
    finally:
        print("\nStarting cleanup...")
        # Cleanup in correct order (child records first)
        try:
            # Remove storage file
            supabase.storage.from_('documents').remove(file_path)
            print("Removed file from storage")
            
            # First delete document chunks
            test_processor.supabase.table('document_chunks')\
                .delete()\
                .eq('document_id', doc_id)\
                .execute()
            print("Deleted document chunks")
            
            # Then delete the document
            test_processor.supabase.table('documents')\
                .delete()\
                .eq('id', doc_id)\
                .execute()
            print("Deleted document")
            
        except Exception as e:
            print(f"Error in cleanup: {str(e)}")