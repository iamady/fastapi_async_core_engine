from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List, Optional

from app.db.session import get_db
from app.schemas.recommendation import RecommendationResponse, RecommendationContext
from app.services.recommendation import RecommendationService

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"]
)


@router.get("/{customer_id}", response_model=RecommendationResponse)
async def get_recommendations_endpoint(
    customer_id: int,
    limit: int = Query(default=5, ge=1, le=20, description="Number of recommendations to return"),
    include_context: bool = Query(default=False, description="Include debugging context"),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized product recommendations for a customer"""
    
    # Initialize recommendation service
    recommendation_service = RecommendationService()
    
    try:
        # Get recommendations
        recommendations_data = await recommendation_service.get_recommendations(
            db, customer_id, limit
        )
        
        if not recommendations_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No recommendations available. Customer may not exist or has no purchase history."
            )
        
        # Format response
        response = RecommendationResponse(
            customer_id=customer_id,
            recommendations=recommendations_data,
            total_recommendations=len(recommendations_data),
            generated_at=datetime.utcnow().isoformat()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating recommendations: {str(e)}"
        )


@router.get("/{customer_id}/context", response_model=RecommendationContext)
async def get_recommendation_context_endpoint(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get recommendation context for debugging and analysis"""
    
    recommendation_service = RecommendationService()
    
    try:
        # Get customer context
        customer_context = await recommendation_service.get_customer_purchase_history(
            db, customer_id
        )
        
        if not customer_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found or has no purchase history"
            )
        
        # Get similar customers
        similar_customers = await recommendation_service.get_similar_customers(
            db, customer_id, limit=5
        )
        
        # Check if LLM is configured
        llm_used = recommendation_service.is_configured()
        
        # Build context response
        context = RecommendationContext(
            customer_name=customer_context.get("customer_name", "Unknown"),
            total_orders=customer_context.get("total_orders", 0),
            total_spent=customer_context.get("total_spent", 0),
            favorite_categories=[cat[0] for cat in customer_context.get("favorite_categories", [])],
            similar_customers_found=len(similar_customers),
            llm_used=llm_used,
            sources_used=["collaborative"]
        )
        
        if llm_used:
            context.sources_used.append("llm")
        
        return context
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting recommendation context: {str(e)}"
        )


@router.get("/{customer_id}/debug", response_model=dict)
async def get_recommendations_debug_endpoint(
    customer_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Debug endpoint to see all recommendation data sources"""
    
    recommendation_service = RecommendationService()
    
    try:
        # Get all data sources
        customer_context = await recommendation_service.get_customer_purchase_history(
            db, customer_id
        )
        
        if not customer_context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found or has no purchase history"
            )
        
        exclude_product_ids = [p['product_id'] for p in customer_context.get('recent_purchases', [])]
        available_products = await recommendation_service.get_available_products(
            db, exclude_product_ids
        )
        
        similar_customers = await recommendation_service.get_similar_customers(
            db, customer_id
        )
        
        collaborative_recommendations = await recommendation_service.get_similar_customers_purchases(
            db, similar_customers, exclude_product_ids
        )
        
        llm_recommendations = []
        if recommendation_service.is_configured():
            llm_recommendations = await recommendation_service.generate_llm_recommendations(
                customer_context,
                available_products,
                collaborative_recommendations
            )
        
        return {
            "customer_context": customer_context,
            "available_products_count": len(available_products),
            "similar_customers_found": len(similar_customers),
            "collaborative_recommendations": collaborative_recommendations,
            "llm_recommendations": llm_recommendations,
            "llm_configured": recommendation_service.is_configured(),
            "final_recommendations": await recommendation_service.get_recommendations(db, customer_id, 5)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in debug endpoint: {str(e)}"
        )
