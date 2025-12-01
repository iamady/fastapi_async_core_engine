from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from .order import OrderRead


class CustomerCreate(BaseModel):
    """Schema for creating a customer"""
    
    name: str
    email: EmailStr


class CustomerRead(BaseModel):
    """Schema for reading a customer"""
    
    id: int
    name: str
    email: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class CustomerWithHistory(CustomerRead):
    """Schema for customer with order history"""
    
    orders: List[OrderRead] = []
