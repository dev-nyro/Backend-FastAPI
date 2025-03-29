import pytest
from ..llm.gemini_client import GeminiClient, gemini_client
import os
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.asyncio
async def test_gemini_response():
    """Test Gemini response generation"""
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
        
    query = "What is machine learning?"
    chunks = [{
        "content": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
    }]
    
    response = await gemini_client.generate_response(query, chunks)
    
    assert response and isinstance(response, str)
    assert len(response) > 0
    # More flexible assertion that works with both mock and real responses
    assert any(term in response.lower() for term in ["machine learning", "ai", "artificial intelligence"])

@pytest.mark.asyncio
async def test_gemini_with_multiple_chunks():
    """Test Gemini with multiple context chunks"""
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
        
    query = "What are the benefits of deep learning?"
    chunks = [
        {
            "content": "Deep learning enables automatic feature extraction from raw data."
        },
        {
            "content": "Deep learning models can handle complex patterns and achieve state-of-the-art results."
        }
    ]
    
    response = await gemini_client.generate_response(query, chunks)
    
    assert response and isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_gemini_error_handling():
    """Test error handling in Gemini client"""
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY not set")
        
    # Test with empty chunks
    response = await gemini_client.generate_response("test query", [])
    assert "Error" in response

    # Test with invalid chunks
    response = await gemini_client.generate_response("test query", None)
    assert "Error" in response