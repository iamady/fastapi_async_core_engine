from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from app.models.order import Order
from app.schemas.order import OrderCreate, OrderRead


async def create_order(db: AsyncSession, order_data: OrderCreate) -> Order:
    """Create a new order"""
    db_order = Order(
        customer_id=order_data.customer_id,
        product_id=order_data.product_id,
        quantity=order_data.quantity
    )
    db.add(db_order)
    await db.commit()
    await db.refresh(db_order)
    return db_order


async def get_order_by_id(db: AsyncSession, order_id: int) -> Optional[Order]:
    """Get order by ID with product details"""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .where(Order.id == order_id)
    )
    return result.scalar_one_or_none()


async def get_orders_by_customer(db: AsyncSession, customer_id: int) -> List[Order]:
    """Get all orders for a specific customer with product details"""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
        .where(Order.customer_id == customer_id)
    )
    return result.scalars().all()


async def get_orders_by_product(db: AsyncSession, product_id: int) -> List[Order]:
    """Get all orders for a specific product"""
    result = await db.execute(
        select(Order).where(Order.product_id == product_id)
    )
    return result.scalars().all()


async def get_all_orders(db: AsyncSession) -> List[Order]:
    """Get all orders with product details"""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.product))
    )
    return result.scalars().all()
