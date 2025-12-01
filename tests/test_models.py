import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order


class TestCustomerModel:
    """Test cases for Customer model."""
    
    @pytest.mark.asyncio
    async def test_create_customer(self, db_session: AsyncSession):
        """Test creating a customer."""
        customer = Customer(
            name="John Doe",
            email="john.doe@example.com"
        )
        
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        assert customer.id is not None
        assert customer.name == "John Doe"
        assert customer.email == "john.doe@example.com"
    
    @pytest.mark.asyncio
    async def test_customer_unique_email(self, db_session: AsyncSession):
        """Test that customer email must be unique."""
        customer1 = Customer(
            name="John Doe",
            email="john@example.com"
        )
        
        customer2 = Customer(
            name="Jane Doe",
            email="john@example.com"  # Same email
        )
        
        db_session.add(customer1)
        await db_session.commit()
        
        db_session.add(customer2)
        with pytest.raises(Exception):  # Should raise integrity error
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_customer_with_orders(self, db_session: AsyncSession):
        """Test customer with related orders."""
        # Create customer
        customer = Customer(
            name="John Doe",
            email="john@example.com"
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        # Create product
        product = Product(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create orders
        order1 = Order(
            customer_id=customer.id,
            product_id=product.id,
            quantity=2
        )
        
        order2 = Order(
            customer_id=customer.id,
            product_id=product.id,
            quantity=1
        )
        
        db_session.add_all([order1, order2])
        await db_session.commit()
        
        # Refresh customer with orders
        result = await db_session.execute(
            select(Customer).where(Customer.id == customer.id)
        )
        customer_with_orders = result.scalar_one()
        
        await db_session.refresh(customer_with_orders, ["orders"])
        
        assert len(customer_with_orders.orders) == 2
        assert customer_with_orders.orders[0].quantity == 2
        assert customer_with_orders.orders[1].quantity == 1


class TestProductModel:
    """Test cases for Product model."""
    
    @pytest.mark.asyncio
    async def test_create_product(self, db_session: AsyncSession):
        """Test creating a product."""
        product = Product(
            name="Test Product",
            category="Electronics",
            price=99.99,
            description="A test product"
        )
        
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.category == "Electronics"
        assert product.price == 99.99
        assert product.description == "A test product"


class TestOrderModel:
    """Test cases for Order model."""
    
    @pytest.mark.asyncio
    async def test_create_order(self, db_session: AsyncSession):
        """Test creating an order."""
        # Create customer
        customer = Customer(
            name="John Doe",
            email="john@example.com"
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        # Create product
        product = Product(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create order
        order = Order(
            customer_id=customer.id,
            product_id=product.id,
            quantity=2
        )
        
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        
        assert order.id is not None
        assert order.customer_id == customer.id
        assert order.product_id == product.id
        assert order.quantity == 2
    
    @pytest.mark.asyncio
    async def test_order_with_relationships(self, db_session: AsyncSession):
        """Test order with customer and product relationships."""
        # Create customer and product
        customer = Customer(
            name="John Doe",
            email="john@example.com"
        )
        db_session.add(customer)
        await db_session.commit()
        await db_session.refresh(customer)
        
        product = Product(
            name="Test Product",
            category="Electronics",
            price=99.99
        )
        db_session.add(product)
        await db_session.commit()
        await db_session.refresh(product)
        
        # Create order
        order = Order(
            customer_id=customer.id,
            product_id=product.id,
            quantity=3
        )
        
        db_session.add(order)
        await db_session.commit()
        await db_session.refresh(order)
        
        # Test relationships
        result = await db_session.execute(
            select(Order).where(Order.id == order.id)
        )
        order_with_relations = result.scalar_one()
        
        await db_session.refresh(order_with_relations, ["customer", "product"])
        
        assert order_with_relations.customer.name == "John Doe"
        assert order_with_relations.product.name == "Test Product"
        assert order_with_relations.product.category == "Electronics"
