import httpx
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.order import Order
from app.models.product import Product
from app.models.customer import Customer


class RecommendationService:
    """Service for generating product recommendations using OpenAI LLM"""
    
    def __init__(self):
        self.api_key = settings.llm_api_key
        self.base_url = settings.llm_base_url
        self.model = settings.llm_model
        
    def is_configured(self) -> bool:
        """Check if LLM is properly configured"""
        return all([self.api_key, self.base_url, self.model])
    
    async def get_customer_purchase_history(
        self, 
        db: AsyncSession, 
        customer_id: int
    ) -> Dict[str, Any]:
        """Get customer's purchase history for recommendation context"""
        # Get customer details
        customer_result = await db.execute(
            select(Customer).where(Customer.id == customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            return {}
        
        # Get customer's orders with product details
        orders_result = await db.execute(
            select(Order)
            .options(selectinload(Order.product))
            .where(Order.customer_id == customer_id)
            .order_by(Order.purchase_date.desc())
        )
        orders = orders_result.scalars().all()
        
        # Get customer's category preferences
        category_counts = {}
        total_spent = 0
        
        for order in orders:
            category = order.product.category
            category_counts[category] = category_counts.get(category, 0) + 1
            total_spent += order.product.price * order.quantity
        
        # Get recently purchased products
        recent_purchases = [
            {
                "product_id": order.product.id,
                "product_name": order.product.name,
                "category": order.product.category,
                "purchase_date": order.purchase_date.isoformat()
            }
            for order in orders[:5]  # Last 5 purchases
        ]
        
        return {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "total_orders": len(orders),
            "total_spent": total_spent,
            "category_preferences": category_counts,
            "recent_purchases": recent_purchases,
            "favorite_categories": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    async def get_available_products(
        self, 
        db: AsyncSession, 
        exclude_product_ids: List[int] = None
    ) -> List[Dict[str, Any]]:
        """Get available products for recommendation"""
        query = select(Product)
        
        if exclude_product_ids:
            query = query.where(Product.id.not_in(exclude_product_ids))
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return [
            {
                "id": product.id,
                "name": product.name,
                "category": product.category,
                "price": product.price,
                "description": product.description or ""
            }
            for product in products
        ]
    
    async def get_similar_customers(
        self, 
        db: AsyncSession, 
        customer_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find customers with similar purchase patterns"""
        # Get target customer's category preferences
        target_orders = await db.execute(
            select(Order.product_id, Product.category)
            .join(Product, Order.product_id == Product.id)
            .where(Order.customer_id == customer_id)
        )
        target_data = target_orders.fetchall()
        target_categories = {row.category for row in target_data}
        
        if not target_categories:
            return []
        
        # Find other customers who bought products in similar categories
        # Using string_agg for SQLite compatibility instead of array_agg
        from sqlalchemy import text
        
        similar_customers_result = await db.execute(
            text("""
                SELECT 
                    o.customer_id,
                    COUNT(o.id) as shared_purchases,
                    GROUP_CONCAT(p.category) as categories
                FROM orders o 
                JOIN products p ON o.product_id = p.id 
                WHERE o.customer_id != :customer_id 
                AND p.category IN :categories
                GROUP BY o.customer_id 
                ORDER BY COUNT(o.id) DESC 
                LIMIT :limit
            """),
            {
                "customer_id": customer_id,
                "categories": tuple(target_categories),
                "limit": limit
            }
        )
        
        similar_customers = similar_customers_result.fetchall()
        
        return [
            {
                "customer_id": row.customer_id,
                "shared_purchases": row.shared_purchases,
                "categories": row.categories.split(',') if row.categories else []
            }
            for row in similar_customers
        ]
    
    async def get_similar_customers_purchases(
        self, 
        db: AsyncSession, 
        similar_customers: List[Dict[str, Any]],
        exclude_product_ids: List[int]
    ) -> List[Dict[str, Any]]:
        """Get what similar customers bought (excluding already purchased items)"""
        if not similar_customers:
            return []
        
        customer_ids = [c["customer_id"] for c in similar_customers]
        
        orders_result = await db.execute(
            select(Order, Product)
            .join(Product, Order.product_id == Product.id)
            .where(
                Order.customer_id.in_(customer_ids),
                Order.product_id.not_in(exclude_product_ids)
            )
            .order_by(Order.purchase_date.desc())
        )
        
        orders = orders_result.fetchall()
        
        # Aggregate by product
        product_stats = {}
        for order, product in orders:
            if product.id not in product_stats:
                product_stats[product.id] = {
                    "product_id": product.id,
                    "product_name": product.name,
                    "category": product.category,
                    "price": product.price,
                    "description": product.description or "",
                    "purchase_count": 0,
                    "customer_count": set()
                }
            
            product_stats[product.id]["purchase_count"] += 1
            product_stats[product.id]["customer_count"].add(order.customer_id)
        
        # Convert to list and sort by popularity
        recommendations = list(product_stats.values())
        for rec in recommendations:
            rec["customer_count"] = len(rec["customer_count"])
        
        recommendations.sort(key=lambda x: (x["purchase_count"], x["customer_count"]), reverse=True)
        return recommendations[:10]  # Top 10 recommendations from similar customers
    
    async def generate_llm_recommendations(
        self,
        customer_context: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        collaborative_recommendations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate recommendations using OpenAI LLM"""
        if not self.is_configured():
            return []
        
        # Prepare context for LLM
        prompt = self._build_recommendation_prompt(
            customer_context, 
            available_products, 
            collaborative_recommendations
        )
        
        try:
            # Make API call to OpenAI-compatible endpoint
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product recommendation expert. Analyze customer purchase history and provide personalized product recommendations. Return recommendations in JSON format with product_id, reason, and confidence_score (0-100)."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.7,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
            
            response.raise_for_status()
            result = response.json()
            
            # Parse LLM response
            content = result["choices"][0]["message"]["content"]
            
            # Try to extract JSON from response
            try:
                # Look for JSON between ```json and ```
                if "```json" in content:
                    json_content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    json_content = content.split("```")[1].split("```")[0]
                else:
                    json_content = content
                
                recommendations = json.loads(json_content)
                
                # Validate and format recommendations
                if isinstance(recommendations, list):
                    return [
                        {
                            "product_id": rec.get("product_id"),
                            "reason": rec.get("reason", ""),
                            "confidence_score": min(100, max(0, rec.get("confidence_score", 50))),
                            "source": "llm"
                        }
                        for rec in recommendations
                        if rec.get("product_id")
                    ]
                elif isinstance(recommendations, dict):
                    return [{
                        "product_id": recommendations.get("product_id"),
                        "reason": recommendations.get("reason", ""),
                        "confidence_score": min(100, max(0, recommendations.get("confidence_score", 50))),
                        "source": "llm"
                    }]
                
            except json.JSONDecodeError:
                # If JSON parsing fails, return empty list
                return []
                
        except Exception as e:
            # Log error but don't fail the entire recommendation
            print(f"LLM recommendation error: {e}")
            return []
    
    def _build_recommendation_prompt(
        self,
        customer_context: Dict[str, Any],
        available_products: List[Dict[str, Any]],
        collaborative_recommendations: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM recommendation"""
        
        # Format customer context
        customer_info = f"""
Customer: {customer_context.get('customer_name', 'Unknown')}
Total Orders: {customer_context.get('total_orders', 0)}
Total Spent: ${customer_context.get('total_spent', 0):.2f}
Favorite Categories: {', '.join([cat[0] for cat in customer_context.get('favorite_categories', [])])}
Recent Purchases: {', '.join([p['product_name'] for p in customer_context.get('recent_purchases', [])[:3]])}
"""
        
        # Format collaborative recommendations
        collab_info = "\n".join([
            f"- {rec['product_name']} (Category: {rec['category']}, Price: ${rec['price']:.2f}) - Bought by {rec['customer_count']} similar customers"
            for rec in collaborative_recommendations[:5]
        ])
        
        # Format available products
        products_info = "\n".join([
            f"- ID: {p['id']}, Name: {p['name']}, Category: {p['category']}, Price: ${p['price']:.2f}"
            for p in available_products[:20]  # Limit to avoid token overflow
        ])
        
        prompt = f"""
Based on the following customer context, provide personalized product recommendations:

{customer_info}

Products bought by similar customers:
{collab_info if collab_info else 'None'}

Available products to recommend:
{products_info}

Please provide 3-5 product recommendations with reasons and confidence scores (0-100).
Return your response as JSON with fields: product_id, reason, confidence_score.
"""
        
        return prompt
    
    async def get_recommendations(
        self,
        db: AsyncSession,
        customer_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get product recommendations for a customer"""
        
        # Get customer context
        customer_context = await self.get_customer_purchase_history(db, customer_id)
        
        if not customer_context:
            return []
        
        # Get products to exclude (already purchased)
        exclude_product_ids = [p['product_id'] for p in customer_context.get('recent_purchases', [])]
        
        # Get available products
        available_products = await self.get_available_products(db, exclude_product_ids)
        
        # Get collaborative filtering recommendations
        similar_customers = await self.get_similar_customers(db, customer_id)
        collaborative_recommendations = await self.get_similar_customers_purchases(
            db, similar_customers, exclude_product_ids
        )
        
        # Get LLM recommendations
        llm_recommendations = await self.generate_llm_recommendations(
            customer_context,
            available_products,
            collaborative_recommendations
        )
        
        # Combine and rank recommendations
        all_recommendations = []
        
        # Add collaborative recommendations with source
        for rec in collaborative_recommendations[:limit]:
            all_recommendations.append({
                "product_id": rec["product_id"],
                "product_name": rec["product_name"],
                "category": rec["category"],
                "price": rec["price"],
                "reason": f"Popular among customers with similar tastes ({rec['customer_count']} customers)",
                "confidence_score": min(100, rec["purchase_count"] * 10 + rec["customer_count"] * 5),
                "source": "collaborative"
            })
        
        # Add LLM recommendations
        for rec in llm_recommendations[:limit]:
            # Find product details
            product = next((p for p in available_products if p["id"] == rec["product_id"]), None)
            if product:
                all_recommendations.append({
                    "product_id": product["id"],
                    "product_name": product["name"],
                    "category": product["category"],
                    "price": product["price"],
                    "reason": rec["reason"],
                    "confidence_score": rec["confidence_score"],
                    "source": "llm"
                })
        
        # Sort by confidence score and remove duplicates
        seen = set()
        unique_recommendations = []
        for rec in sorted(all_recommendations, key=lambda x: x["confidence_score"], reverse=True):
            if rec["product_id"] not in seen:
                seen.add(rec["product_id"])
                unique_recommendations.append(rec)
        
        return unique_recommendations[:limit]
