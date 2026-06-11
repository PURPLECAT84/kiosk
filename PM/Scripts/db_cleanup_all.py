# PM/Scripts/db_cleanup_all.py
import sys
import os

# Backend 폴더를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backend'))

from database import DB_session
from models.user import UserInfo, BusinessInfo
from models.kiosk import Kiosk
from models.kiosk_admin import KioskAdmin
from models.shelve import Shelve
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem

def clean_database_all():
    db = DB_session()
    try:
        # 외래키 제약조건을 고려한 순차적 전체 삭제
        print("[PROCESS] OrderItem 테이블 삭제 중...")
        db.query(OrderItem).delete(synchronize_session=False)
        
        print("[PROCESS] Order 테이블 삭제 중...")
        db.query(Order).delete(synchronize_session=False)
        
        print("[PROCESS] Product 테이블 삭제 중...")
        db.query(Product).delete(synchronize_session=False)
        
        print("[PROCESS] Category 테이블 삭제 중...")
        db.query(Category).delete(synchronize_session=False)
        
        print("[PROCESS] Shelve 테이블 삭제 중...")
        db.query(Shelve).delete(synchronize_session=False)
        
        print("[PROCESS] KioskAdmin 테이블 삭제 중...")
        db.query(KioskAdmin).delete(synchronize_session=False)
        
        print("[PROCESS] Kiosk 테이블 삭제 중...")
        db.query(Kiosk).delete(synchronize_session=False)
        
        print("[PROCESS] BusinessInfo 테이블 삭제 중...")
        db.query(BusinessInfo).delete(synchronize_session=False)
        
        print("[PROCESS] UserInfo 테이블 삭제 중...")
        db.query(UserInfo).delete(synchronize_session=False)
        
        db.commit()
        print("[SUCCESS] 데이터베이스의 모든 테스트용 및 더미 데이터가 정상적으로 완전히 삭제되었습니다. (초기화 완료)")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] 클린업 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    clean_database_all()
