from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerWithHistory


async def create_customer(db: AsyncSession, customer_data: CustomerCreate) -> Customer:
    """Create a new customer"""
    db_customer = Customer(
        name=customer_data.name,
        email=customer_data.email
    )
    db.add(db_customer)
    await db.commit()
    await db.refresh(db_customer)
    return db_customer


async def get_customer_by_id(db: AsyncSession, customer_id: int) -> Optional[Customer]:
    """Get customer by ID"""
    result = await db.execute(
        select(Customer).where(Customer.id == customer_id)
    )
    return result.scalar_one_or_none()


async def get_customer_with_history(db: AsyncSession, customer_id: int) -> Optional[CustomerWithHistory]:
    """Get customer with order history"""
    result = await db.execute(
        select(Customer)
        .options(selectinload(Customer.orders).selectinload(Customer.orders.property.mapper.class_.product))
        .where(Customer.id == customer_id)
    )
    customer = result.scalar_one_or_none()
    
    if customer:
        # Convert to CustomerWithHistory schema
        return CustomerWithHistory(
            id=customer.id,
            name=customer.name,
            email=customer.email,
            created_at=customer.created_at,
            orders=[
                {
                    "id": order.id,
                    "customer_id": order.customer_id,
                    "product_id": order.product_id,
                    "quantity": order.quantity,
                    "purchase_date": order.purchase_date,
                    "product": {
                        "id": order.product.id,
                        "name": order.product.name,
                        "category": order.product.category,
                        "price": order.product.price,
                        "description": order.product.description
                    } if order.product else None
                }
                for order in customer.orders
            ]
        )
    return None


async def get_all_customers(db: AsyncSession) -> List[Customer]:
    """Get all customers"""
    result = await db.execute(select(Customer))
    return result.scalars().all()
