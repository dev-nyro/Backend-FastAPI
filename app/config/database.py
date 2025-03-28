from supabase import create_client, Client
from . import settings

def get_supabase_client(use_service_role: bool = False) -> Client:
    try:
        key = settings.supabase_service_key if use_service_role else settings.supabase_key
        
        # Create client without options
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=key,
        )
        
        return client

    except Exception as e:
        print(f"Failed to initialize Supabase client: {e}")
        raise
