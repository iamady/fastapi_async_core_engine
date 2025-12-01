import json
from typing import List, Dict, Any, Optional
from openai import AsyncOpenAI

from app.core.config import settings


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
        if not self.is_configured():
            return []
        
        # Build system prompt
        system_prompt = "You are a helpful shopping assistant. Return pure JSON."
        
        # Build user prompt with purchase history
        history_text = "\n".join([f"- {item}" for item in purchase_history])
        user_prompt = f"Given these past purchases:\n{history_text}\n\nRecommend 3 items."
        
        try:
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # Extract response content
            content = response.choices[0].message.content
            
            # Parse JSON response
            recommendations = self._parse_ai_response(content)
            
            return recommendations
            
        except Exception as e:
            # Log error but don't fail the entire request
            print(f"AI recommendation error: {e}")
            return []
    
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
