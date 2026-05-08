from sqlalchemy import String,ForeignKey,Integer,DateTime
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid
from datetime import datetime

class Order(Base):
    __tablename__ = "order_info"
    id : Mapped[int] = mapped_column(primary_key = True, index = True)
    store_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("store_info.id"), nullable=False)
    total_amount : Mapped[int] = mapped_column(Integer,nullable=False)
    payment_method : Mapped[str] = mapped_column(String,nullable = False)
    payment_provider : Mapped[str] = mapped_column(String, nullable = False)
    approval_code : Mapped[str] = mapped_column(String, nullable = False)
    status : Mapped[str] = mapped_column(String, default="Completed")
    created_date : Mapped[datetime] = mapped_column(DateTime, default=datetime.now)    

   
    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")