from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class AIRecommendationItem(BaseModel):
    """Schema for a single AI recommendation item"""
    
    item: str
    reason: str
    confidence: int  # 0-100


class AIRecommendationResponse(BaseModel):
    """Schema for AI recommendation response"""
    
    customer_id: int
    recommendations: List[AIRecommendationItem]
    total_recommendations: int
    source: str = "ai"
    generated_at: str


class PurchaseHistoryRequest(BaseModel):
    """Schema for purchase history request"""
    
    purchase_history: List[str]
