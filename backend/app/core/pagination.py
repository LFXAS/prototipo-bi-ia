from __future__ import annotations

from pydantic import BaseModel, Field


class PageRead[Item](BaseModel):
    """Stable paginated API response shared by administrative resources."""

    items: list[Item]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
