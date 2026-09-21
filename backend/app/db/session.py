from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

engine = create_async_engine(
    get_settings().postgres_async_url,
    pool_pre_ping=True,
    echo=get_settings().app_debug,
)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        yield session


# Nombre homogéneo para los módulos nuevos; se mantiene get_db_session por compatibilidad.
get_session = get_db_session
async_session_factory = AsyncSessionFactory


async def dispose_engine() -> None:
    await engine.dispose()
