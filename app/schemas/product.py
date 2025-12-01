from pydantic import BaseModel
from typing import Optional


class ProductCreate(BaseModel):
    """Schema for creating a product"""
    
    name: str
    category: str
    price: float
    description: Optional[str] = None


class ProductRead(BaseModel):
    """Schema for reading a product"""
    
    id: int
    name: str
    category: str
    price: float
    description: Optional[str] = None
    
    class Config:
        from_attributes = True
