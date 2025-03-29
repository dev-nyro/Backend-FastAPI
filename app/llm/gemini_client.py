import google.generativeai as genai
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

class MockGeminiClient:
    async def generate_response(self, query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        """Mock implementation for testing"""
        if not relevant_chunks:
            return "Error: No context provided"
        return f"This is a mock response about {query} based on the provided context: {relevant_chunks[0]['content']}"

class GeminiClient:
    def __init__(self, use_mock: bool = False):
        if use_mock:
            self.mock_client = MockGeminiClient()
            return
            
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        
        try:
            # Use the newer Gemini 1.5 Flash model directly
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Set generation config
            self.model.generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
        except Exception as e:
            print(f"Error during model initialization: {str(e)}")
            raise ValueError(f"Failed to initialize Gemini model: {str(e)}")
    
    async def generate_response(self, query: str, relevant_chunks: List[Dict[str, Any]]) -> str:
        if hasattr(self, 'mock_client'):
            return await self.mock_client.generate_response(query, relevant_chunks)
            
        try:
            if not relevant_chunks:
                return "Error: No context provided"
                
            context = "\n".join([chunk["content"] for chunk in relevant_chunks])
            prompt = f"""Based on the following context, provide a detailed answer to the question.
            
            Context: {context}
            
            Question: {query}
            
            Answer the question using only the information from the context above."""
            
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                return "Error: Empty response from LLM"
            return response.text
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "Error generating response from LLM"

# Singleton instance - use mock in test environment
is_test = os.getenv("PYTEST_CURRENT_TEST") is not None
gemini_client = GeminiClient(use_mock=is_test)