from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.subscription_model import Subscription, SubscriptionCreate, SubscriptionUpdate
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from datetime import datetime
from typing import List
from uuid import UUID

router = APIRouter(
    prefix="/subscriptions",  # Ensure this matches the test's expected path
    tags=["Subscriptions"],
    dependencies=[Depends(auth_middleware)]
)

@router.post("/", response_model=Subscription)
async def create_subscription(subscription: SubscriptionCreate, request: Request):
    """Create a new subscription (admin only)"""
    try:
        user = request.state.user
        if user.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="Only admins can create subscriptions")
        
        supabase = get_supabase_client(use_service_role=True)
        
        # Convert the model to dict and prepare data
        subscription_data = {
            "company_id": str(subscription.company_id),
            "plan_type": subscription.plan_type,
            "max_documents": subscription.max_documents,
            "max_queries": subscription.max_queries,
            "start_date": subscription.start_date.isoformat(),
            "end_date": subscription.end_date.isoformat()
        }
        
        print(f"Processed subscription data: {subscription_data}")  # Debug print
        
        response = supabase.table('subscriptions').insert(subscription_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create subscription")
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error creating subscription: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Subscription])
async def get_subscriptions(request: Request):
    """Get subscriptions (filtered by company if not admin)"""
    user = request.state.user
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        query = supabase.table('subscriptions').select("*")
        
        # If not admin, only show company's subscriptions
        if user.get('role') != 'admin':
            query = query.eq('company_id', user.get('company_id'))
            
        response = query.execute()
        return response.data if response.data else []
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{subscription_id}", response_model=Subscription)
async def get_subscription(subscription_id: UUID, request: Request):
    """Get a specific subscription"""
    user = request.state.user
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        query = supabase.table('subscriptions').select("*").eq('id', str(subscription_id))
        
        # If not admin, verify company_id matches
        if user.get('role') != 'admin':
            query = query.eq('company_id', user.get('company_id'))
            
        response = query.execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{subscription_id}", response_model=Subscription)
async def update_subscription(subscription_id: UUID, subscription: SubscriptionUpdate, request: Request):
    """Update a subscription (admin only)"""
    user = request.state.user
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update subscriptions")
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Verify subscription exists
        existing = supabase.table('subscriptions')\
            .select("*")\
            .eq('id', str(subscription_id))\
            .execute()
            
        if not existing.data:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Only include non-None values from the update model
        update_data = {k: v for k, v in subscription.model_dump().items() if v is not None}
        
        response = supabase.table('subscriptions')\
            .update(update_data)\
            .eq('id', str(subscription_id))\
            .execute()
            
        return response.data[0]
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error updating subscription: {str(e)}")  # Debug print
        raise HTTPException(status_code=500, detail=str(e))