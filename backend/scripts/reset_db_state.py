import asyncio
from app.db.session import AsyncSessionLocal
from app.models.domain import Product, MerchantPolicy
from sqlalchemy import update

async def reset_db_records():
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(Product)
            .values(stock=10, category="laptop")
        )
        await db.execute(
            update(MerchantPolicy)
            .values(max_autonomous_purchase=70000.0)
        )
        await db.commit()
        print("Database state cleaned & restored successfully!")

if __name__ == "__main__":
    asyncio.run(reset_db_records())
