from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List

from app.db.session import get_db
from app.schemas.ai_recommendation import AIRecommendationResponse
from app.services.ai_service import AIService
from app.services.customer import get_customer_by_id
from app.services.order import get_orders_by_customer


router = APIRouter(
    prefix="/customers",
    tags=["AI Recommendations"]
)


@router.post("/{customer_id}/recommendations", response_model=AIRecommendationResponse)
async def get_ai_recommendations_endpoint(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-powered product recommendations for a customer
    POST /customers/{id}/recommendations
    """
    
    # Initialize AI service
    ai_service = AIService()
    
    try:
        # Verify customer exists
        customer = await get_customer_by_id(db, customer_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found"
            )
        
        # Get customer's purchase history
        orders = await get_orders_by_customer(db, customer_id)
        
        if not orders:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No purchase history found for this customer"
            )
        
        # Build purchase history list
        purchase_history = []
        for order in orders:
            product_name = order.product.name if order.product else "Unknown Product"
            category = order.product.category if order.product else "Unknown Category"
            purchase_history.append(f"{product_name} (Category: {category})")
        
        # Get AI recommendations
        ai_recommendations = await ai_service.get_recommendations(purchase_history)
        
        if not ai_recommendations:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to generate recommendations at this time. AI service may be unavailable."
            )
        
        # Format response
        response = AIRecommendationResponse(
            customer_id=customer_id,
            recommendations=ai_recommendations,
            total_recommendations=len(ai_recommendations),
            source="ai",
            generated_at=datetime.utcnow().isoformat()
        )
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating AI recommendations: {str(e)}"
        )
