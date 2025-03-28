from ..config.database import get_supabase_client
from fastapi import HTTPException
from datetime import datetime
import pytz

async def check_document_limits(company_id: str):
    """Check if company has reached document limits"""
    supabase = get_supabase_client(use_service_role=True)
    
    try:
        # Get active subscription
        subscription = supabase.table('subscriptions')\
            .select("*")\
            .eq('company_id', company_id)\
            .order('start_date', desc=True)\
            .limit(1)\
            .execute()
            
        if not subscription.data:
            raise HTTPException(
                status_code=403,
                detail="No active subscription found"
            )
            
        subscription_data = subscription.data[0]
        
        # Count current documents
        docs_count = supabase.table('documents')\
            .select("id", count='exact')\
            .eq('company_id', company_id)\
            .execute()
            
        count = docs_count.count if hasattr(docs_count, 'count') else len(docs_count.data)
        
        if count >= subscription_data['max_documents']:
            raise HTTPException(
                status_code=403,
                detail=f"Document limit reached for current subscription (max: {subscription_data['max_documents']})"
            )
            
        return subscription_data
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error checking subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def get_subscription(company_id: str):
    """Get active subscription for company"""
    supabase = get_supabase_client(use_service_role=True)
    
    try:
        response = supabase.table('subscriptions')\
            .select("*")\
            .eq('company_id', company_id)\
            .order('created_at', desc=True)\
            .limit(1)\
            .execute()
            
        return response.data[0] if response.data else None
        
    except Exception as e:
        print(f"Error getting subscription: {str(e)}")
        return None

__all__ = ['check_document_limits', 'get_subscription']