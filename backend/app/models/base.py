from datetime import datetime
from typing import Any, Dict, Optional
from sqlmodel import Field, SQLModel


class BaseTSModel:
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now, nullable=False)


class BaseTSIDModel(BaseTSModel):
    id: int = Field(default=None, primary_key=True)
