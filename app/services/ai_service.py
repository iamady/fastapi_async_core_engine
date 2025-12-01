import json
import logging
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.core.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class AIService:
    """AI service for generating recommendations using OpenAI-compatible API"""
    
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured"""
        return all([self.client.api_key, settings.llm_base_url, self.model])
    
    async def get_recommendations(self, purchase_history: List[str]) -> List[Dict[str, Any]]:
        """
        Get AI recommendations based on purchase history
        
        Args:
            purchase_history: List of past purchase descriptions
            
        Returns:
            List of recommended items with details
        """
        logger.info(f"AI Service: Getting recommendations for purchase history: {purchase_history}")
        
        # Check if AI is configured
        if not self.is_configured():
            logger.warning("AI Service: Not configured, using fallback recommendations")
            logger.info(f"AI Service: LLM_API_KEY: {'***' if settings.llm_api_key else 'None'}")
            logger.info(f"AI Service: LLM_BASE_URL: {settings.llm_base_url}")
            logger.info(f"AI Service: LLM_MODEL: {settings.llm_model}")
            return self._get_fallback_recommendations(purchase_history)
        
        logger.info(f"AI Service: Using model '{self.model}' with base URL '{settings.llm_base_url}'")
        
        # Build enhanced system prompt
        system_prompt = """You are a helpful shopping assistant specialized in e-commerce recommendations. 
        Analyze the customer's purchase history and provide 3 specific product recommendations.
        Return ONLY pure JSON with NO additional text before or after.
        Use this exact format:
        [
            {
                "item": "Product Name",
                "reason": "Clear explanation why this matches their interests",
                "confidence": 75
            }
        ]
        The item should be a realistic product name, not generic terms like 'electronics' or 'clothing'."""
        
        # Build enhanced user prompt with context
        history_text = "\n".join([f"- {item}" for item in purchase_history])
        user_prompt = f"""Customer Purchase History:
{history_text}

Based on this customer's purchase history, recommend 3 specific products they would be interested in.
Consider:
1. Complementary products to their purchases
2. Related items in the same category
3. Popular items that match their interests

Return exactly 3 recommendations in JSON format. Each item should have:
- item: Specific product name (e.g., 'Wireless Mouse', 'Cookbook', 'Running Shoes')
- reason: Why this recommendation fits their profile (2-3 sentences)
- confidence: 0-100 score based on how well it matches their history

IMPORTANT: Return ONLY the JSON array, no other text."""
        
        logger.debug(f"AI Service: System prompt: {system_prompt}")
        logger.debug(f"AI Service: User prompt: {user_prompt}")
        
        try:
            logger.info("AI Service: Making API call to LLM...")
            
            # Make API call with enhanced parameters
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,  # Balanced creativity
                max_tokens=800,   # Increased for detailed responses
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            logger.info(f"AI Service: API call successful, response usage: {getattr(response, 'usage', 'N/A')}")
            
            # Extract response content
            content = response.choices[0].message.content
            logger.debug(f"AI Service: Raw AI response: {content}")
            
            # Parse JSON response
            recommendations = self._parse_ai_response(content)
            
            logger.info(f"AI Service: Parsed {len(recommendations)} recommendations from AI response")
            
            # If AI didn't return valid recommendations, use fallback
            if not recommendations:
                logger.warning("AI Service: AI returned no valid recommendations, using fallback")
                return self._get_fallback_recommendations(purchase_history)
            
            logger.info(f"AI Service: Successfully generated {len(recommendations)} AI recommendations")
            return recommendations
            
        except Exception as e:
            # Log detailed error information
            logger.error(f"AI Service: API call failed with error: {e}", exc_info=True)
            logger.error(f"AI Service: Falling back to rule-based recommendations")
            
            # Fallback to rule-based recommendations
            return self._get_fallback_recommendations(purchase_history)
    
    def _parse_ai_response(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse AI response and extract recommendations
        
        Args:
            content: Raw AI response content
            
        Returns:
            List of parsed recommendations
        """
        try:
            # Try to extract JSON from response
            if "```json" in content:
                json_content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_content = content.split("```")[1].split("```")[0]
            else:
                json_content = content
            
            # Parse JSON
            parsed = json.loads(json_content)
            
            # Validate and format recommendations
            if isinstance(parsed, list):
                return [
                    {
                        "item": rec.get("item", ""),
                        "reason": rec.get("reason", ""),
                        "confidence": min(100, max(0, rec.get("confidence", 50)))
                    }
                    for rec in parsed
                    if rec.get("item")
                ]
            elif isinstance(parsed, dict):
                return [{
                    "item": parsed.get("item", ""),
                    "reason": parsed.get("reason", ""),
                    "confidence": min(100, max(0, parsed.get("confidence", 50)))
                }]
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract recommendations from text
            return self._extract_from_text(content)
        
        return []
    
    def _get_fallback_recommendations(self, purchase_history: List[str]) -> List[Dict[str, Any]]:
        """
        Generate rule-based recommendations when AI is not available
        
        Args:
            purchase_history: List of past purchase descriptions
            
        Returns:
            List of fallback recommendations based on purchase patterns
        """
        logger.info(f"AI Service: Using fallback recommendations for history: {purchase_history}")
        
        recommendations = []
        
        # Analyze purchase history for patterns
        history_text = " ".join(purchase_history).lower()
        logger.debug(f"AI Service: Analyzing history text: {history_text}")
        
        # Define recommendation rules based on categories and products from products.json
        rules = [
            # Electronics recommendations (from products.json)
            {
                "keywords": ["laptop", "zenbook", "computer", "notebook"],
                "recommendations": [
                    {"item": "AlphaSound Wireless ANC Earbuds", "reason": "Premium audio companion for your laptop", "confidence": 90},
                    {"item": "Bluetooth Fitness Smartwatch", "reason": "Sync with your laptop for productivity", "confidence": 85},
                    {"item": "Wireless Ergonomic Keyboard & Mouse Combo", "reason": "Enhance your laptop setup", "confidence": 80}
                ]
            },
            {
                "keywords": ["earbuds", "alphaSound", "audio", "headphones"],
                "recommendations": [
                    {"item": "Noise-Cancelling Over-Ear Headphones", "reason": "Alternative high-quality audio option", "confidence": 85},
                    {"item": "Bluetooth Fitness Smartwatch", "reason": "Perfect companion for active lifestyle", "confidence": 80},
                    {"item": "USB-C 65W Fast Charger Adapter", "reason": "Essential charging solution", "confidence": 75}
                ]
            },
            {
                "keywords": ["smartwatch", "fitness", "bluetooth"],
                "recommendations": [
                    {"item": "AlphaSound Wireless ANC Earbuds", "reason": "Great for workouts and daily use", "confidence": 85},
                    {"item": "Wireless Ergonomic Keyboard & Mouse Combo", "reason": "Complete your smart setup", "confidence": 80},
                    {"item": "USB-C 65W Fast Charger Adapter", "reason": "Keep all devices charged", "confidence": 75}
                ]
            },
            # Clothing recommendations (from products.json)
            {
                "keywords": ["jacket", "denim", "heritage", "outerwear"],
                "recommendations": [
                    {"item": "Urban Stretch Slim Fit Chinos", "reason": "Perfect pairing with your jacket", "confidence": 85},
                    {"item": "Classic Polo Shirt (Men)", "reason": "Great layering option", "confidence": 80},
                    {"item": "Unisex Cotton Crew-Neck T-Shirt (Pack of 2)", "reason": "Versatile base layer", "confidence": 75}
                ]
            },
            {
                "keywords": ["jeans", "chinos", "pants", "trousers"],
                "recommendations": [
                    {"item": "Classic Leather Belt (Brown)", "reason": "Essential accessory for pants", "confidence": 90},
                    {"item": "Classic Polo Shirt (Men)", "reason": "Complete your casual look", "confidence": 85},
                    {"item": "Athletic Running Shorts (Unisex)", "reason": "Versatile addition to wardrobe", "confidence": 80}
                ]
            },
            {
                "keywords": ["dress", "maxi", "boho", "fashion"],
                "recommendations": [
                    {"item": "Classic Leather Belt (Brown)", "reason": "Accent your dress perfectly", "confidence": 85},
                    {"item": "Unisex Cotton Crew-Neck T-Shirt (Pack of 2)", "reason": "Comfortable casual option", "confidence": 80},
                    {"item": "Athletic Running Shorts (Unisex)", "reason": "Great for layering", "confidence": 75}
                ]
            },
            # Books recommendations (from products.json)
            {
                "keywords": ["python", "programming", "mastering", "coding", "sqlalchemy"],
                "recommendations": [
                    {"item": "Deep Learning Essentials: From Scratch to Production", "reason": "Advance your technical skills", "confidence": 95},
                    {"item": "History of Ancient Civilizations (Vol. I)", "reason": "Expand your knowledge base", "confidence": 85},
                    {"item": "Mindfulness & Minimalist Living", "reason": "Balance technical work with mindfulness", "confidence": 80}
                ]
            },
            {
                "keywords": ["cookbook", "cooking", "culinary", "recipes"],
                "recommendations": [
                    {"item": "The Quantum Architect (Hardcover)", "reason": "Inspire creativity beyond cooking", "confidence": 85},
                    {"item": "Mindfulness & Minimalist Living", "reason": "Complement your cooking lifestyle", "confidence": 80},
                    {"item": "Children's Illustrated Fairy Tales", "reason": "Perfect for family cooking time", "confidence": 75}
                ]
            },
            # Home recommendations (from products.json)
            {
                "keywords": ["bed sheet", "bedding", "cotton", "sleep"],
                "recommendations": [
                    {"item": "LED Desk Lamp with Adjustable Arm", "reason": "Perfect reading companion", "confidence": 90},
                    {"item": "Memory Foam Lumbar Support Cushion", "reason": "Enhance your bedroom seating", "confidence": 85},
                    {"item": "Aroma Scented Candle (Pack of 3)", "reason": "Create cozy bedroom atmosphere", "confidence": 80}
                ]
            },
            {
                "keywords": ["bookshelf", "storage", "organization", "wall-mount"],
                "recommendations": [
                    {"item": "LED Desk Lamp with Adjustable Arm", "reason": "Perfect for your organized workspace", "confidence": 85},
                    {"item": "Memory Foam Lumbar Support Cushion", "reason": "Comfort for long organizing sessions", "confidence": 80},
                    {"item": "Cotton Canvas Storage Box (Set of 3)", "reason": "Additional storage solutions", "confidence": 75}
                ]
            }
        ]
        
        # Apply rules to generate recommendations
        applied_rules = set()
        
        for rule in rules:
            # Check if any keyword matches
            if any(keyword in history_text for keyword in rule["keywords"]):
                rule_name = "_".join(rule["keywords"][:2])  # Use first 2 keywords as rule identifier
                if rule_name not in applied_rules:
                    logger.info(f"AI Service: Matched rule with keywords: {rule['keywords']}")
                    # Add recommendations from this rule
                    for rec in rule["recommendations"]:
                        recommendations.append(rec)
                    applied_rules.add(rule_name)
        
        # If no rules matched, provide general recommendations from products.json
        if not recommendations:
            logger.warning("AI Service: No specific rules matched, using general recommendations")
            recommendations = [
                {"item": "Premium Merino Wool V-Neck Sweater", "reason": "Timeless wardrobe essential", "confidence": 80},
                {"item": "4K Smart LED TV 55\"", "reason": "Popular home entertainment choice", "confidence": 75},
                {"item": "Men's Waterproof Windbreaker Jacket", "reason": "Practical and versatile option", "confidence": 70}
            ]
        
        # Limit to 3 recommendations and ensure uniqueness
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec["item"] not in seen:
                seen.add(rec["item"])
                unique_recommendations.append(rec)
            if len(unique_recommendations) >= 3:
                break
        
        logger.info(f"AI Service: Generated {len(unique_recommendations)} fallback recommendations")
        return unique_recommendations
    
    def _extract_from_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Fallback method to extract recommendations from plain text
        
        Args:
            content: AI response content as text
            
        Returns:
            List of extracted recommendations
        """
        recommendations = []
        
        # Split by lines and look for numbered items
        lines = content.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for patterns like "1. Item name" or "- Item name"
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or line.startswith('- ')):
                # Extract item name (remove numbering)
                item_text = line.split('.', 1)[-1].strip() if '.' in line else line[2:].strip()
                
                recommendations.append({
                    "item": item_text,
                    "reason": "Based on your purchase history",
                    "confidence": 50
                })
                
                # Limit to 3 recommendations
                if len(recommendations) >= 3:
                    break
        
        return recommendations
