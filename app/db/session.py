from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession,async_sessionmaker,create_async_engine
from collections.abc import AsyncGenerator


# creataing async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo = settings.DEBUG,
    future = True,
    pool_pre_ping = True,
)

# create session factory
AsyncSessionLocal = AsyncSession(
    bind = engine,
    class_= AsyncSession,
    expire_on_commit = False,
    autoflush = False,
)

# fastapi dependecy to inject into routes
async def get_db()->AsyncGenerator[AsyncSession,None]:
    async with AsyncSessionLocal as session:
        try:
            yield session
        finally:
            await session.close()
