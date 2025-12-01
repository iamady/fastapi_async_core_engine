from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.customer import CustomerCreate, CustomerRead, CustomerWithHistory
from app.services.customer import create_customer, get_customer_by_id, get_customer_with_history

router = APIRouter(
    prefix="/customers",
    tags=["customers"]
)


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer_endpoint(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new customer"""
    try:
        customer = await create_customer(db, customer_data)
        return customer
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating customer: {str(e)}"
        )


@router.get("/{customer_id}/history", response_model=CustomerWithHistory)
async def get_customer_history_endpoint(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get customer with order history"""
    customer_with_history = await get_customer_with_history(db, customer_id)
    
    if not customer_with_history:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    return customer_with_history
