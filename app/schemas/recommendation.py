from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal


class RecommendationItem(BaseModel):
    """Schema for a single product recommendation"""
    
    product_id: int
    product_name: str
    category: str
    price: Decimal
    reason: str
    confidence_score: int  # 0-100
    source: str  # "collaborative" or "llm"


class RecommendationResponse(BaseModel):
    """Schema for recommendation response"""
    
    customer_id: int
    recommendations: List[RecommendationItem]
    total_recommendations: int
    generated_at: str


class RecommendationContext(BaseModel):
    """Schema for recommendation context/debugging"""
    
    customer_name: str
    total_orders: int
    total_spent: Decimal
    favorite_categories: List[str]
    similar_customers_found: int
    llm_used: bool
    sources_used: List[str]
