import sys
from pathlib import Path
from os import getenv
from dotenv import load_dotenv
import os
import bcrypt  # Change to use bcrypt directly

# Add absolute path for root directory
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Load environment variables from .env file
try:
    env_path = root_dir / '.env'
    load_dotenv(env_path)
    
    # Debug output
    print("Environment variables loaded from:", env_path)
    print("SUPABASE_URL:", getenv("SUPABASE_URL"))
    print("SUPABASE_SERVICE_KEY:", getenv("SUPABASE_SERVICE_KEY", "")[:10] + "..." if getenv("SUPABASE_SERVICE_KEY") else "Not set")
except Exception as e:
    print(f"Error loading .env file: {e}")
    sys.exit(1)

from supabase import create_client
from uuid import uuid4
from datetime import datetime

def get_supabase_admin_client():
    url = getenv("SUPABASE_URL")
    service_key = getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        raise ValueError(
            "Missing required environment variables. "
            "Please ensure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in .env"
        )
    
    try:
        # Create client without options parameter - the headers will be handled internally
        return create_client(
            supabase_url=url,
            supabase_key=service_key
        )
    except Exception as e:
        print(f"Error creating Supabase client: {e}")
        raise

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def init_db():
    # Use service role client instead of normal client
    supabase = get_supabase_admin_client()
    
    try:
        # 1. Create initial company if not exists
        company_response = supabase.table('companies')\
            .select("*")\
            .eq('email', 'admin@company.com')\
            .execute()
            
        if company_response.data:
            company_id = company_response.data[0]['id']
            print(f"Company already exists with ID: {company_id}")
        else:
            company_id = str(uuid4())
            company_data = {
                "id": company_id,
                "name": "Admin Company",
                "email": "admin@company.com",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table('companies').insert(company_data).execute()
            print(f"Company created with ID: {company_id}")
        
        # 2. Check if admin user exists
        admin_email = "admin@test.com"
        user_response = supabase.table('users')\
            .select("*")\
            .eq('email', admin_email)\
            .execute()
            
        hashed_password = hash_password("adminpass123")
        user_data = {
            "email": admin_email,
            "hashed_password": hashed_password,
            "full_name": "Admin User",
            "role": "admin",
            "company_id": company_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        if user_response.data:
            # Update existing user
            user_id = user_response.data[0]['id']
            supabase.table('users')\
                .update(user_data)\
                .eq('id', user_id)\
                .execute()
            print(f"Admin user updated with ID: {user_id}")
        else:
            # Create new user
            response = supabase.table('users').insert(user_data).execute()
            print(f"Admin user created with ID: {response.data[0]['id']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    init_db()