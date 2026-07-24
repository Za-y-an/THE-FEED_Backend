import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:yourlocalpassword@localhost/the_feed"
)

# Render and Neon require SSL, but your local machine does not.
# We dynamically add the SSL argument only if connecting to the cloud.
connect_args = {"ssl": "require"} if "render.com" in DATABASE_URL or "neon.tech" in DATABASE_URL else {}

engine = create_async_engine(DATABASE_URL, echo=False, connect_args=connect_args)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session