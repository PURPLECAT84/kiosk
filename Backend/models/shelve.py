from sqlalchemy import String, DateTime, ForeignKey
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from models.store import Store
    from models.category import Category
    from models.product import Product

class Shelve(Base):
    __tablename__ = "shelve_info"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4, index=True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stores.id"), nullable=False) 
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    terminal_id: Mapped[str] = mapped_column(String, nullable=False)
    business_number: Mapped[str] = mapped_column(String, nullable=False)
    vender_code: Mapped[str] = mapped_column(String, nullable=False)

    store = relationship("Store", back_populates="shelves")
    categories = relationship("Category", back_populates="shelve", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="shelve", cascade="all, delete-orphan")