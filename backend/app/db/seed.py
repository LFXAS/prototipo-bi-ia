"""Loads the approved, non-secret baseline catalog after database migrations.

This module deliberately contains no business or personal data. It creates the
minimum protected security catalog required to access a fresh local environment.
It can be executed repeatedly: the operation is idempotent and safe for an
existing developer database.
"""

from __future__ import annotations

import asyncio

from app.db.session import async_session_factory, dispose_engine
from app.modules.security.service import seed_security


async def seed_application_data() -> None:
    """Apply the approved baseline catalog using the application's database session."""
    async with async_session_factory() as session:
        await seed_security(session)


async def main() -> None:
    try:
        await seed_application_data()
    finally:
        await dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
