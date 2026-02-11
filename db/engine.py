from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from db.models import Base
from core.config import config

engine = create_async_engine(config.database_url, echo=False)
AsyncSessionFactory = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Сидируем gate-каналы из .env если БД пустая
    await seed_gate_channels()


async def seed_gate_channels() -> None:
    """При первом запуске переносит каналы из .env в БД."""
    from db.repository import GateChannelRepo
    from core.config import config as cfg

    async with AsyncSessionFactory() as session:
        repo = GateChannelRepo(session)
        if await repo.count() == 0 and cfg.channels:
            for ch in cfg.channels:
                await repo.add(username=ch.username, title=ch.name)