from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .product import ProductRead


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    
    customer_id: int
    product_id: int
    quantity: int


class OrderRead(BaseModel):
    """Schema for reading an order"""
    
    id: int
    customer_id: int
    product_id: int
    quantity: int
    purchase_date: datetime
    
    # Nested product details
    product: Optional[ProductRead] = None
    
    class Config:
        from_attributes = True
