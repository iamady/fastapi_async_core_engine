import pytest
import json
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.customer import create_customer, get_customer_by_id, get_customer_with_history
from app.services.order import create_order, get_order_by_id
from app.services.product import create_product
from app.services.ai_service import AIService
from app.schemas.customer import CustomerCreate
from app.schemas.order import OrderCreate
from app.schemas.product import ProductCreate


class TestCustomerService:
    """Test cases for customer service functions."""
    
    @pytest.mark.asyncio
    async def test_create_customer_service(self, db_session: AsyncSession):
        """Test creating a customer via service."""
        customer_data = CustomerCreate(
            name="John Doe",
            email="john.doe@example.com"
        )
        
        customer = await create_customer(db_session, customer_data)
        
        assert customer.id is not None
        assert customer.name == customer_data.name
        assert customer.email == customer_data.email
    
    @pytest.mark.asyncio
    async def test_get_customer_by_id_service(self, db_session: AsyncSession):
        """Test getting customer by ID via service."""
        # Create customer directly in DB
        customer = CustomerCreate(
            name="John Doe",
            email="john@example.com"
        )
        
        created_customer = await create_customer(db_session, customer)
        
        # Get customer by ID
        retrieved_customer = await get_customer_by_id(db_session, created_customer.id)
        
        assert retrieved_customer is not None
        assert retrieved_customer.id == created_customer.id
        assert retrieved_customer.name == created_customer.name
        assert retrieved_customer.email == created_customer.email
    
    @pytest.mark.asyncio
    async def test_get_customer_by_id_not_found(self, db_session: AsyncSession):
        """Test getting non-existent customer returns None."""
        customer = await get_customer_by_id(db_session, 999)
        
        assert customer is None
    
    @pytest.mark.asyncio
    async def test_get_customer_with_history_service(self, db_session: AsyncSession):
        """Test getting customer with order history via service."""
        # Create customer and product
        customer_data = CustomerCreate(
            name="John Doe",
            email="john@example.com"
        )
        customer = await create_customer(db_session, customer_data)
        
        product_data = ProductCreate(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        product = await create_product(db_session, product_data)
        
        # Create order
        order_data = OrderCreate(
            customer_id=customer.id,
            product_id=product.id,
            quantity=2
        )
        await create_order(db_session, order_data)
        
        # Get customer with history
        customer_with_history = await get_customer_with_history(db_session, customer.id)
        
        assert customer_with_history is not None
        assert customer_with_history.id == customer.id
        assert customer_with_history.name == customer.name
        assert len(customer_with_history.orders) == 1
        
        order = customer_with_history.orders[0]
        assert order.customer_id == customer.id
        assert order.product_id == product.id
        assert order.quantity == 2
        assert order.product.name == product.name


class TestOrderService:
    """Test cases for order service functions."""
    
    @pytest.mark.asyncio
    async def test_create_order_service(self, db_session: AsyncSession):
        """Test creating an order via service."""
        # Create customer and product
        customer_data = CustomerCreate(
            name="John Doe",
            email="john@example.com"
        )
        customer = await create_customer(db_session, customer_data)
        
        product_data = ProductCreate(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        product = await create_product(db_session, product_data)
        
        # Create order
        order_data = OrderCreate(
            customer_id=customer.id,
            product_id=product.id,
            quantity=2
        )
        
        order = await create_order(db_session, order_data)
        
        assert order.id is not None
        assert order.customer_id == customer.id
        assert order.product_id == product.id
        assert order.quantity == 2
    
    @pytest.mark.asyncio
    async def test_get_order_by_id_service(self, db_session: AsyncSession):
        """Test getting order by ID via service."""
        # Create customer and product
        customer_data = CustomerCreate(
            name="John Doe",
            email="john@example.com"
        )
        customer = await create_customer(db_session, customer_data)
        
        product_data = ProductCreate(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        product = await create_product(db_session, product_data)
        
        # Create order
        order_data = OrderCreate(
            customer_id=customer.id,
            product_id=product.id,
            quantity=2
        )
        created_order = await create_order(db_session, order_data)
        
        # Get order by ID
        retrieved_order = await get_order_by_id(db_session, created_order.id)
        
        assert retrieved_order is not None
        assert retrieved_order.id == created_order.id
        assert retrieved_order.customer_id == customer.id
        assert retrieved_order.product_id == product.id
        assert retrieved_order.quantity == 2
        assert retrieved_order.product.name == product.name


class TestAIService:
    """Test cases for AI service."""
    
    @pytest.mark.asyncio
    async def test_ai_service_not_configured_fallback(self):
        """Test AI service uses fallback when not configured."""
        # Create AI service without configuration
        ai_service = AIService()
        
        # Mock settings to be empty
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.llm_api_key = None
            mock_settings.llm_base_url = None
            mock_settings.llm_model = None
            
            # Test with purchase history
            purchase_history = ["Test Product (Category: Electronics)"]
            recommendations = await ai_service.get_recommendations(purchase_history)
            
            # Should return fallback recommendations
            assert len(recommendations) > 0
            assert all("item" in rec for rec in recommendations)
            assert all("reason" in rec for rec in recommendations)
            assert all("confidence" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_ai_service_with_mocked_api(self):
        """Test AI service with mocked API call."""
        # Mock settings
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.llm_api_key = "test-key"
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_model = "gpt-3.5-turbo"
            
            ai_service = AIService()
            
            # Mock the OpenAI client
            with patch('app.services.ai_service.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client
                
                # Mock API response
                mock_response = AsyncMock()
                mock_response.choices = [AsyncMock()]
                mock_response.choices[0].message.content = json.dumps([
                    {
                        "item": "Mocked Product",
                        "reason": "This is a mocked recommendation",
                        "confidence": 85
                    }
                ])
                mock_client.chat.completions.create.return_value = mock_response
                
                # Test with purchase history
                purchase_history = ["Test Product (Category: Electronics)"]
                recommendations = await ai_service.get_recommendations(purchase_history)
                
                # Should return AI recommendations
                assert len(recommendations) == 1
                assert recommendations[0]["item"] == "Mocked Product"
                assert recommendations[0]["reason"] == "This is a mocked recommendation"
                assert recommendations[0]["confidence"] == 85
    
    @pytest.mark.asyncio
    async def test_ai_service_api_failure_fallback(self):
        """Test AI service falls back when API fails."""
        # Mock settings
        with patch('app.services.ai_service.settings') as mock_settings:
            mock_settings.llm_api_key = "test-key"
            mock_settings.llm_base_url = "https://api.openai.com/v1"
            mock_settings.llm_model = "gpt-3.5-turbo"
            
            ai_service = AIService()
            
            # Mock the OpenAI client to raise exception
            with patch('app.services.ai_service.AsyncOpenAI') as mock_openai:
                mock_client = AsyncMock()
                mock_openai.return_value = mock_client
                
                mock_client.chat.completions.create.side_effect = Exception("API Error")
                
                # Test with purchase history
                purchase_history = ["Test Product (Category: Electronics)"]
                recommendations = await ai_service.get_recommendations(purchase_history)
                
                # Should fall back to rule-based recommendations
                assert len(recommendations) > 0
                assert all("item" in rec for rec in recommendations)
                assert all("reason" in rec for rec in recommendations)
                assert all("confidence" in rec for rec in recommendations)
