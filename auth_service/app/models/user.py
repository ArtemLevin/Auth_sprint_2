from __future__ import annotations
from datetime import datetime
from uuid import UUID as PyUUID, uuid4
from typing import List, Optional

from sqlalchemy import String, Boolean, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth_service.app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[PyUUID] = mapped_column(primary_key=True, default=uuid4)
    login: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100))
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    roles: Mapped[List["UserRole"]] = relationship("UserRole", back_populates="user")
    history: Mapped[List["LoginHistory"]] = relationship(
        "LoginHistory", back_populates="user"
    )
