#!/usr/bin/env python3
"""
Seed script for Customer Orders & Recommendation Engine (CORE)
Generates sample data using products.json: 10 customers, products from JSON, 5 orders per customer

Usage:
    python seed.py                    # Normal seeding (keeps existing data)
    python seed.py --reset            # Reset database and re-seed
    python seed.py --reset --force    # Force reset without confirmation
"""

import asyncio
import random
import sys
import json
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import engine, AsyncSessionLocal
from app.db.base import Base
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order


class DataSeeder:
    """Async data seeder using Faker with re-seeding capabilities"""
    
    def __init__(self, reset_db: bool = False, force_reset: bool = False):
        self.faker = Faker()
        self.faker.seed_instance(42)  # For reproducible data
        self.reset_db = reset_db
        self.force_reset = force_reset
        
    async def create_customers(self, db: AsyncSession, count: int = 10) -> list[Customer]:
        """Create sample customers"""
        print(f"Creating {count} customers...")
        
        customers = []
        for i in range(count):
            customer = Customer(
                name=self.faker.name(),
                email=self.faker.unique.email()
            )
            customers.append(customer)
        
        db.add_all(customers)
        await db.commit()
        
        # Refresh to get IDs
        for customer in customers:
            await db.refresh(customer)
        
        print(f"✓ Created {len(customers)} customers")
        return customers
    
    async def create_products(self, db: AsyncSession) -> list[Product]:
        """Create sample products from products.json"""
        print("Creating products from products.json...")
        
        # Load products from JSON file
        try:
            with open('products.json', 'r', encoding='utf-8') as f:
                products_data = json.load(f)
        except FileNotFoundError:
            print("❌ products.json not found, using fallback data")
            products_data = self._get_fallback_products()
        
        products = []
        for product_data in products_data:
            product = Product(
                name=product_data['name'],
                category=product_data['category'],
                price=Decimal(str(product_data['price'])),
                description=product_data['description']
            )
            products.append(product)
        
        db.add_all(products)
        await db.commit()
        
        # Refresh to get IDs
        for product in products:
            await db.refresh(product)
        
        print(f"✓ Created {len(products)} products from products.json")
        return products
    
    def _get_fallback_products(self):
        """Fallback product data if products.json is not available"""
        return [
            {
                "name": "Classic Denim Jacket",
                "category": "Clothing",
                "price": 2499.99,
                "description": "Timeless denim jacket perfect for casual wear"
            },
            {
                "name": "Wireless Earbuds",
                "category": "Electronics",
                "price": 2599.99,
                "description": "Premium wireless earbuds with noise cancellation"
            },
            {
                "name": "Python Programming Guide",
                "category": "Books",
                "price": 1499.00,
                "description": "Comprehensive guide to Python programming"
            },
            {
                "name": "Cotton Bed Sheet Set",
                "category": "Home",
                "price": 2999.99,
                "description": "Soft cotton bed sheet set for comfortable sleep"
            }
        ]
    
    async def create_orders(self, db: AsyncSession, customers: list[Customer], products: list[Product], orders_per_customer: int = 5) -> list[Order]:
        """Create sample orders for each customer"""
        print(f"Creating {orders_per_customer} orders per customer...")
        
        orders = []
        current_time = datetime.utcnow()
        
        for customer in customers:
            for _ in range(orders_per_customer):
                # Random date in the last 6 months
                days_ago = random.randint(1, 180)
                purchase_date = current_time - timedelta(days=days_ago)
                
                order = Order(
                    customer_id=customer.id,
                    product_id=random.choice(products).id,
                    quantity=random.randint(1, 3),
                    purchase_date=purchase_date
                )
                orders.append(order)
        
        db.add_all(orders)
        await db.commit()
        
        print(f"✓ Created {len(orders)} orders")
        return orders
    
    async def confirm_reset(self) -> bool:
        """Ask user for confirmation before resetting database"""
        if self.force_reset:
            return True
        
        response = input("\n⚠️  This will DELETE all existing data and re-seed the database. Continue? (y/N): ")
        return response.lower() in ['y', 'yes']
    
    async def reset_database(self):
        """Drop and recreate all tables"""
        print("🧹 Resetting database...")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Database reset completed")
    
    async def check_existing_data(self) -> dict:
        """Check if data already exists"""
        async with AsyncSessionLocal() as db:
            # Count customers
            customer_result = await db.execute(select(func.count()).select_from(Customer))
            customer_count = customer_result.scalar()
            
            # Count products
            product_result = await db.execute(select(func.count()).select_from(Product))
            product_count = product_result.scalar()
            
            # Count orders
            order_result = await db.execute(select(func.count()).select_from(Order))
            order_count = order_result.scalar()
            
            return {
                'customers': customer_count or 0,
                'products': product_count or 0,
                'orders': order_count or 0,
                'has_data': (customer_count or 0) > 0 or (product_count or 0) > 0 or (order_count or 0) > 0
            }
    
    async def seed_data(self):
        """Main seeding function"""
        print("🚀 Starting data seeding process...")
        print("=" * 50)
        
        # Handle database reset if requested
        if self.reset_db:
            if not await self.confirm_reset():
                print("❌ Seeding cancelled by user")
                return
            
            await self.reset_database()
        
        # Check existing data
        existing_data = await self.check_existing_data()
        if existing_data['has_data']:
            print(f"📊 Existing data found:")
            print(f"   • Customers: {existing_data['customers']}")
            print(f"   • Products: {existing_data['products']}")
            print(f"   • Orders: {existing_data['orders']}")
            
            if not self.reset_db:
                print("💡 Tip: Use --reset flag to clear existing data and re-seed")
                print("❌ Seeding cancelled to avoid duplicate data")
                return
        
        # Ensure tables are created
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with AsyncSessionLocal() as db:
            try:
                # Create customers
                customers = await self.create_customers(db, 10)
                
                # Create products
                products = await self.create_products(db)
                
                # Create orders
                orders = await self.create_orders(db, customers, products, 5)
                
                print("=" * 50)
                print("✅ Seeding completed successfully!")
                print(f"📊 Summary:")
                print(f"   • Customers: {len(customers)}")
                print(f"   • Products: {len(products)}")
                print(f"   • Orders: {len(orders)}")
                print(f"   • Total Records: {len(customers) + len(products) + len(orders)}")
                
            except Exception as e:
                print(f"❌ Error during seeding: {e}")
                await db.rollback()
                raise


async def main():
    """Main entry point"""
    # Parse command line arguments
    reset_db = "--reset" in sys.argv
    force_reset = "--force" in sys.argv
    
    if force_reset and not reset_db:
        print("❌ Error: --force flag requires --reset flag")
        print("Usage: python seed.py --reset --force")
        return 1
    
    try:
        # Initialize seeder
        seeder = DataSeeder(reset_db=reset_db, force_reset=force_reset)
        
        # Run seeding
        await seeder.seed_data()
        
        print("\n🎉 Database seeding completed!")
        print("You can now run your FastAPI application with sample data.")
        
    except Exception as e:
        print(f"\n💥 Seeding failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
