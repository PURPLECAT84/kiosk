from sqlalchemy import String,ForeignKey,Integer
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
    payment_method : Mapped[str] = mapped_column(String, ForeignKey, nullable = False)
    payment_provider : Mapped[str | None] = mapped_column(String, nullable = False)
    approval_code : Mapped[str | None] = mapped_column(String, nullable = False)
    status : Mapped[str] = mapped_column(String, default="Completed")
    created_date : Mapped[datetime] = mapped_column(datetime, default=datetime.now)    

   
    store = relationship("Store", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_item"
    id : Mapped[uuid.UUID] = mapped_column(Uuid, primary_key = True, index = True)
    order_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("order_info.id"), nullable=False)
    product_id : Mapped[uuid.UUID] = mapped_column(ForeignKey("product_list.id"), nullable=True)# 상품이 삭제되어도 영수증 내역은 유지되어야 하기 때문에 nullable=True
    quantity : Mapped[int] = mapped_column(Integer, default=1)

    # 상품명이 바뀌거나 삭제되어도 영수증 내역은 유지되어야 함
    product_name : Mapped[str] = mapped_column(String, nullable=False)
    product_price : Mapped[int] = mapped_column(Integer, nullable=False)

    
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")