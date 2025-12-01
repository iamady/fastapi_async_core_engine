from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductRead


async def create_product(db: AsyncSession, product_data: ProductCreate) -> Product:
    """Create a new product"""
    db_product = Product(
        name=product_data.name,
        category=product_data.category,
        price=product_data.price,
        description=product_data.description
    )
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


async def get_product_by_id(db: AsyncSession, product_id: int) -> Optional[Product]:
    """Get product by ID"""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    return result.scalar_one_or_none()


async def get_all_products(db: AsyncSession) -> List[Product]:
    """Get all products"""
    result = await db.execute(select(Product))
    return result.scalars().all()
