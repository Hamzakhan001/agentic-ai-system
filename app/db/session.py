from __future__ import annotations

from sqlmodel import Session, SQLModel, create_engine

from app.core.config import get_settings

from app.db.memory_models import models
from app.db import models

settings = get_settings()
engine = create_engine(settings.database_url, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
