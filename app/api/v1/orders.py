from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.order import OrderCreate, OrderRead
from app.services.order import create_order, get_order_by_id
from app.services.customer import get_customer_by_id
from app.services.product import get_product_by_id

router = APIRouter(
    prefix="/orders",
    tags=["orders"]
)


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order_endpoint(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new order"""
    # Validate customer exists
    customer = await get_customer_by_id(db, order_data.customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found"
        )
    
    # Validate product exists
    product = await get_product_by_id(db, order_data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        order = await create_order(db, order_data)
        return order
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating order: {str(e)}"
        )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order_endpoint(
    order_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get order by ID"""
    order = await get_order_by_id(db, order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order
