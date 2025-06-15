from datetime import datetime
from uuid import UUID as PyUUID, uuid4
from typing import List, Optional
from app.models.base import Base

from sqlalchemy import (
    String,
    Text,
    DateTime,
    func,
    ForeignKey,
    ARRAY,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    DeclarativeBase,
)


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[PyUUID] = mapped_column(primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    permissions: Mapped[List[str]] = mapped_column(ARRAY(String(255)), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    users: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="role")
