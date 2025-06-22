from __future__ import annotations
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base
from uuid import UUID as PyUUID


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[PyUUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role_id: Mapped[PyUUID] = mapped_column(ForeignKey("roles.id"), primary_key=True)

    user: Mapped["User"] = relationship("User", back_populates="roles")
    role: Mapped["Role"] = relationship("Role", back_populates="users")
