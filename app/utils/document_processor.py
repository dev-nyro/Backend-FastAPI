from typing import List, Dict, Any
import json
from datetime import datetime
import uuid
from ..config.database import get_supabase_client
import PyPDF2
import io

class DocumentProcessor:
    def __init__(self):
        self.supabase = get_supabase_client(use_service_role=True)

    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        pdf_file = io.BytesIO(file_content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text

    def create_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Split text into chunks using a simple approach"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_len = len(word) + 1  # +1 for space
            if current_length + word_len > chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = []
                current_length = 0
            current_chunk.append(word)
            current_length += word_len
            
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return chunks

    async def process_document(self, document_id: str):
        """Process a document"""
        print(f"Starting to process document: {document_id}")
        try:
            # Get the document
            response = self.supabase.table('documents')\
                .select('*')\
                .eq('id', document_id)\
                .execute()

            if not response.data:
                raise Exception(f"Document {document_id} not found")

            document = response.data[0]

            # Get file content from storage
            storage_response = self.supabase\
                .storage\
                .from_('documents')\
                .download(document['file_path'])

            # Extract text based on file type
            text = ""
            if document['file_type'].lower() == 'pdf':
                text = self.extract_text_from_pdf(storage_response)
            else:
                # Add support for other file types as needed
                raise Exception(f"Unsupported file type: {document['file_type']}")

            # Create chunks
            chunks = self.create_chunks(text)
            
            # Create chunk records
            chunk_records = [
                {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "chunk_index": idx,
                    "content": chunk,
                    "metadata": {"page": 1},  # Simplified for MVP
                    "embedding_id": None,
                    "created_at": datetime.utcnow().isoformat(),
                    "vector_status": "pending"
                }
                for idx, chunk in enumerate(chunks)
            ]

            # Insert chunks in batches of 50
            for i in range(0, len(chunk_records), 50):
                batch = chunk_records[i:i + 50]
                self.supabase.table('document_chunks').insert(batch).execute()

            # Update document status
            update_data = {
                "status": "processed",
                "updated_at": datetime.utcnow().isoformat(),
                "chunk_count": len(chunks)
            }

            self.supabase.table('documents')\
                .update(update_data)\
                .eq('id', document_id)\
                .execute()

            return {"status": "success", "message": "Document processed successfully"}

        except Exception as e:
            print(f"Error processing document {document_id}: {str(e)}")
            self.supabase.table('documents')\
                .update({
                    "status": "failed",
                    "updated_at": datetime.utcnow().isoformat()
                })\
                .eq('id', document_id)\
                .execute()
            raise e

# Singleton instance
document_processor = DocumentProcessor()