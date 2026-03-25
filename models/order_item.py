from sqlalchemy import String,ForeignKey,Integer
from database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid
from sqlalchemy.types import Uuid
from datetime import datetime




class OrderItem(Base):
    __tablename__ = "order_item"
    id : Mapped[uuid.UUID] = mapped_column(default=uuid.uuid4,   primary_key = True, index = True)
    order_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("order_info.id"), nullable=False)
    product_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("product_list.id"), nullable=True)# 상품이 삭제되어도 영수증 내역은 유지되어야 하기 때문에 nullable=True
    quantity : Mapped[int] = mapped_column(Integer, default=1)

    # 상품명이 바뀌거나 삭제되어도 영수증 내역은 유지되어야 함
    product_name : Mapped[str] = mapped_column(String, nullable=False)
    product_price : Mapped[int] = mapped_column(Integer, nullable=False)

    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")