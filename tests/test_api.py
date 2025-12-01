import pytest
import json
from unittest.mock import AsyncMock, patch

from tests.conftest import test_customer_data, test_product_data, test_order_data
from fastapi.testclient import TestClient


class TestCustomerAPI:
    """Test cases for customer-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_customer(self, client: TestClient, test_customer_data: dict):
        """Test creating a new customer."""
        response = await client.post("/customers", json=test_customer_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["name"] == test_customer_data["name"]
        assert data["email"] == test_customer_data["email"]
        assert "id" in data
        assert "created_at" in data
    
    @pytest.mark.asyncio
    async def test_create_customer_duplicate_email(self, client: TestClient, test_customer_data: dict):
        """Test creating a customer with duplicate email should fail."""
        # Create first customer
        await client.post("/customers", json=test_customer_data)
        
        # Try to create another with same email
        duplicate_data = test_customer_data.copy()
        duplicate_data["name"] = "Jane Doe"
        
        response = await client.post("/customers", json=duplicate_data)
        
        # Should fail with 500 due to unique constraint
        assert response.status_code == 500
    
    @pytest.mark.asyncio
    async def test_get_customer_history_empty(self, client: TestClient, test_customer_data: dict):
        """Test getting customer history when no orders exist."""
        # Create customer
        create_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_response.json()["id"]
        
        # Get customer history
        response = await client.get(f"/customers/{customer_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == customer_id
        assert data["name"] == test_customer_data["name"]
        assert data["email"] == test_customer_data["email"]
        assert data["orders"] == []
    
    @pytest.mark.asyncio
    async def test_get_customer_history_with_orders(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test getting customer history with existing orders."""
        # Create customer
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        # Create product
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Update order data with actual IDs
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        # Create order
        create_order_response = await client.post("/orders", json=order_data)
        assert create_order_response.status_code == 201
        
        # Get customer history
        response = await client.get(f"/customers/{customer_id}/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == customer_id
        assert len(data["orders"]) == 1
        
        order = data["orders"][0]
        assert order["customer_id"] == customer_id
        assert order["product_id"] == product_id
        assert order["quantity"] == order_data["quantity"]
        assert "product" in order
        assert order["product"]["name"] == test_product_data["name"]
        assert order["product"]["category"] == test_product_data["category"]


class TestOrderAPI:
    """Test cases for order-related API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_order(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test creating a new order."""
        # Create customer
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        # Create product
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Update order data with actual IDs
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        # Create order
        response = await client.post("/orders", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["customer_id"] == customer_id
        assert data["product_id"] == product_id
        assert data["quantity"] == order_data["quantity"]
        assert "id" in data
        assert "purchase_date" in data
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_customer(self, client: TestClient, test_order_data: dict):
        """Test creating an order with invalid customer ID."""
        order_data = test_order_data.copy()
        order_data["customer_id"] = 999  # Non-existent customer
        
        response = await client.post("/orders", json=order_data)
        
        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_product(self, client: TestClient, test_customer_data: dict, test_order_data: dict):
        """Test creating an order with invalid product ID."""
        # Create customer
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        # Update order data
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = 999  # Non-existent product
        
        response = await client.post("/orders", json=order_data)
        
        assert response.status_code == 404
        assert "Product not found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_order_by_id(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test getting an order by ID."""
        # Create customer and product
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Create order
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        create_order_response = await client.post("/orders", json=order_data)
        order_id = create_order_response.json()["id"]
        
        # Get order by ID
        response = await client.get(f"/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == order_id
        assert data["customer_id"] == customer_id
        assert data["product_id"] == product_id
        assert data["quantity"] == order_data["quantity"]
        assert "product" in data
        assert data["product"]["name"] == test_product_data["name"]


class TestAIRecommendationsAPI:
    """Test cases for AI recommendation API endpoints."""
    
    @pytest.mark.asyncio
    async def test_get_ai_recommendations_no_history(self, client: TestClient, test_customer_data: dict):
        """Test getting AI recommendations for customer with no purchase history."""
        # Create customer
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        # Get recommendations
        response = await client.post(f"/customers/{customer_id}/recommendations")
        
        assert response.status_code == 503
        assert "No purchase history found" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_ai_recommendations_with_history_no_ai_config(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test getting AI recommendations with purchase history but no AI configuration (fallback mode)."""
        # Create customer and product
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Create order (purchase history)
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        await client.post("/orders", json=order_data)
        
        # Get recommendations (should use fallback since AI is not configured)
        response = await client.post(f"/customers/{customer_id}/recommendations")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["customer_id"] == customer_id
        assert len(data["recommendations"]) > 0
        assert data["total_recommendations"] == len(data["recommendations"])
        assert data["source"] == "ai"
        
        # Check recommendation structure
        for rec in data["recommendations"]:
            assert "item" in rec
            assert "reason" in rec
            assert "confidence" in rec
            assert isinstance(rec["item"], str)
            assert isinstance(rec["reason"], str)
            assert isinstance(rec["confidence"], int)
            assert 0 <= rec["confidence"] <= 100
    
    @pytest.mark.asyncio
    async def test_get_ai_recommendations_with_mocked_ai(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test getting AI recommendations with mocked AsyncOpenAI call."""
        # Create customer and product
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Create order (purchase history)
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        await client.post("/orders", json=order_data)
        
        # Mock AI response
        mock_ai_response = [
            {
                "item": "Mocked Recommendation",
                "reason": "This is a mocked recommendation for testing",
                "confidence": 85
            }
        ]
        
        with patch('app.services.ai_service.AsyncOpenAI') as mock_openai:
            # Set up the mock
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].message.content = json.dumps(mock_ai_response)
            mock_client.chat.completions.create.return_value = mock_response
            
            # Get recommendations
            response = await client.post(f"/customers/{customer_id}/recommendations")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["customer_id"] == customer_id
            assert len(data["recommendations"]) == 1
            assert data["recommendations"][0]["item"] == "Mocked Recommendation"
            assert data["recommendations"][0]["reason"] == "This is a mocked recommendation for testing"
            assert data["recommendations"][0]["confidence"] == 85
    
    @pytest.mark.asyncio
    async def test_get_ai_recommendations_ai_api_failure(self, client: TestClient, test_customer_data: dict, test_product_data: dict, test_order_data: dict):
        """Test getting AI recommendations when AI API fails (should fallback to rule-based)."""
        # Create customer and product
        create_customer_response = await client.post("/customers", json=test_customer_data)
        customer_id = create_customer_response.json()["id"]
        
        create_product_response = await client.post("/products", json=test_product_data)
        product_id = create_product_response.json()["id"]
        
        # Create order (purchase history)
        order_data = test_order_data.copy()
        order_data["customer_id"] = customer_id
        order_data["product_id"] = product_id
        
        await client.post("/orders", json=order_data)
        
        # Mock AI API failure
        with patch('app.services.ai_service.AsyncOpenAI') as mock_openai:
            # Set up the mock to raise an exception
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            mock_client.chat.completions.create.side_effect = Exception("AI API Error")
            
            # Get recommendations (should fallback to rule-based)
            response = await client.post(f"/customers/{customer_id}/recommendations")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["customer_id"] == customer_id
            assert len(data["recommendations"]) > 0
            assert data["source"] == "ai"
    
    @pytest.mark.asyncio
    async def test_get_ai_recommendations_nonexistent_customer(self, client: TestClient):
        """Test getting AI recommendations for non-existent customer."""
        response = await client.post("/customers/999/recommendations")
        
        assert response.status_code == 404
        assert "Customer not found" in response.json()["detail"]


class TestHealthEndpoint:
    """Test cases for health endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client: TestClient):
        """Test the health check endpoint."""
        response = await client.get("/health")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
