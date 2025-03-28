from fastapi import APIRouter, Depends, HTTPException, Request
from ..models.company_model import Company, CompanyCreate, CompanyUpdate
from ..config.database import get_supabase_client
from ..auth.auth_middleware import auth_middleware
from datetime import datetime
from typing import List
from uuid import UUID

router = APIRouter(
    prefix="/companies",
    tags=["Companies"],
    dependencies=[Depends(auth_middleware)],
    # Add this to handle both with and without trailing slash
    redirect_slashes=False
)

@router.get("/", response_model=List[Company])
async def get_companies(request: Request):
    """Get all companies (admin only)"""
    user = request.state.user
    print(f"User data from token: {user}")  # Debug info
    
    # Enable role check
    if user.get('role') != 'admin':
        print(f"Access denied. User role: {user.get('role')}")  # Debug info
        raise HTTPException(status_code=403, detail="Only admins can view all companies")
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        print("Fetching companies with service role...")
        
        # Simplified query without filters first
        response = supabase.table('companies').select("*").execute()
        
        print(f"Raw Supabase response: {response}")  # Debug full response
        print(f"Response data: {response.data}")
        print(f"Number of companies found: {len(response.data) if response.data else 0}")
        
        if not response.data:
            print("No companies found in database")
            return []
        
        # Transform the data to match the Company model
        companies = []
        for company in response.data:
            try:
                companies.append({
                    "id": company.get("id"),
                    "name": company.get("name"),
                    "email": company.get("email"),
                    "created_at": company.get("created_at"),
                    "updated_at": company.get("updated_at"),
                    "is_active": company.get("is_active", True)
                })
            except Exception as e:
                print(f"Error processing company {company}: {e}")
        
        return companies
        
    except Exception as e:
        print(f"Error in get_companies: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{company_id}", response_model=Company)
async def get_company(company_id: UUID, request: Request):
    """Get a specific company"""
    user = request.state.user
    print(f"User data from token: {user}")  # Debug info
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        response = supabase.table('companies').select("*").eq('id', str(company_id)).execute()
        
        if not response.data:
            print(f"Company not found with ID: {company_id}")  # Debug info
            raise HTTPException(status_code=404, detail="Company not found")
        
        company = response.data[0]
        
        # Allow admin access or users viewing their own company
        if user.get('role') != 'admin' and str(company_id) != user.get('company_id'):
            print(f"Access denied. User role: {user.get('role')}, User company: {user.get('company_id')}, Requested company: {company_id}")
            raise HTTPException(status_code=403, detail="Not authorized to view this company")
        
        return company
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Error in get_company: {str(e)}")  # Debug info
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_model=Company)
async def create_company(company: CompanyCreate, request: Request):
    """Create a new company (admin only)"""
    user = request.state.user
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can create companies")
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Check for duplicate email
        existing = supabase.table('companies').select("*").eq('email', company.email).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Company with this email already exists")
        
        company_data = company.model_dump()
        company_data["created_at"] = datetime.utcnow().isoformat()
        company_data["updated_at"] = datetime.utcnow().isoformat()
        company_data["is_active"] = True
        
        response = supabase.table('companies').insert(company_data).execute()
        return response.data[0]
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{company_id}", response_model=Company)
async def update_company(company_id: UUID, company: CompanyUpdate, request: Request):
    """Update a company (admin only)"""
    if request.state.user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can update companies")
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Check if company exists
        existing = supabase.table('companies').select("*").eq('id', str(company_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Filter out None values and prepare update data
        update_data = {}
        if company.name is not None:
            update_data["name"] = company.name
        if company.email is not None:
            update_data["email"] = company.email
        if company.is_active is not None:
            update_data["is_active"] = company.is_active
            
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
        
        # Debug info
        print(f"Updating company {company_id} with data: {update_data}")
        
        response = supabase.table('companies').update(update_data).eq('id', str(company_id)).execute()
        return response.data[0]
    except Exception as e:
        print(f"Error updating company: {str(e)}")  # Debug info
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{company_id}")
async def delete_company(company_id: UUID, request: Request):
    """Delete (soft-delete) a company (admin only)"""
    if request.state.user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Only admins can delete companies")
    
    try:
        supabase = get_supabase_client(use_service_role=True)
        
        # Check if company exists
        existing = supabase.table('companies').select("*").eq('id', str(company_id)).execute()
        if not existing.data:
            raise HTTPException(status_code=404, detail="Company not found")
        
        # Soft delete with proper datetime formatting
        update_data = {
            "is_active": False,
            "updated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
        }
        
        # Debug info
        print(f"Soft deleting company {company_id} with data: {update_data}")
        
        response = supabase.table('companies').update(update_data).eq('id', str(company_id)).execute()
        return {"message": "Company deleted successfully"}
    except Exception as e:
        print(f"Error deleting company: {str(e)}")  # Debug info
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ['router']