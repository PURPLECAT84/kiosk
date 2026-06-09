# core/seeder.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from models.user import UserInfo, UserRole
from models.store import Store
from models.kiosk import Kiosk
from models.shelve import Shelve
from models.category import Category
from models.product import Product
from core.security import get_password_hash

def seed_initial_data(db: Session):
    """
    [초보자용 교보재 지침 - 시더 기능]
    이 함수는 프로그램 구동 시 데이터베이스에 테스트용 기본 가맹점 및 키오스크 데이터를 보장(Seeding)합니다.
    이를 통해 신규 실행 환경에서도 백엔드와 키오스크 클라이언트가 404 에러 없이 완벽히 연동됩니다.
    초보자들은 이 코드를 통해 어떻게 특정 UUID 값을 테이블 간 관계성에 맞춰 미리 밀어넣는지 배울 수 있습니다.
    """
    # 1. 테스트용 사장님(MANAGER) 계정 보장
    # 'dummy1@moki.com' 계정이 없으면 비밀번호 '88888888'로 생성합니다.
    manager_email = "dummy1@moki.com"
    stmt = select(UserInfo).where(UserInfo.email == manager_email)
    manager_user = db.execute(stmt).scalars().first()
    
    if not manager_user:
        manager_user = UserInfo(
            email=manager_email,
            password=get_password_hash("88888888"),
            name="김점주 사장님",
            role=UserRole.MANAGER,
            is_active=True
        )
        db.add(manager_user)
        db.commit()
        db.refresh(manager_user)

    # 2. 테스트용 개발자(DEV) 계정 보장 (dev@moki.com / 88888888)
    dev_email = "dev@moki.com"
    stmt = select(UserInfo).where(UserInfo.email == dev_email)
    dev_user = db.execute(stmt).scalars().first()
    
    if not dev_user:
        dev_user = UserInfo(
            email=dev_email,
            password=get_password_hash("88888888"),
            name="모키 개발자",
            role=UserRole.DEV,
            is_active=True
        )
        db.add(dev_user)
        db.commit()
        db.refresh(dev_user)

    # 3. 키오스크 클라이언트가 기본으로 조회하는 UUID 고정 매장 정보 보장 (88888888-8888-8888-8888-888888888888)
    target_uuid = uuid.UUID("88888888-8888-8888-8888-888888888888")
    stmt = select(Store).where(Store.id == target_uuid)
    store = db.execute(stmt).scalars().first()
    
    if not store:
        store = Store(
            id=target_uuid,
            code="ST8888",
            name="모키 반점",
            address="서울시 보라구 행복동 88-8",
            type="Restaurant", # 외식형 키오스크 매장
            owner_name="김점주",
            user_id=manager_user.id,
            status="ACTIVE"
        )
        db.add(store)
        db.commit()
        db.refresh(store)

    # 4. 고정 UUID 키오스크 기기 보장
    stmt = select(Kiosk).where(Kiosk.id == target_uuid)
    kiosk = db.execute(stmt).scalars().first()
    
    if not kiosk:
        kiosk = Kiosk(
            id=target_uuid,
            code="KS888888",
            store_id=store.id,
            name="모키반점 입구 키오스크",
            model_name="MOKI-A1",
            type="Restaurant",
            status="OPERATING",
            payment_status="NORMAL"
        )
        db.add(kiosk)
        db.commit()
        db.refresh(kiosk)

    # 5. 매대(Shelve) 보장
    stmt = select(Shelve).where(Shelve.store_id == store.id)
    shelve = db.execute(stmt).scalars().first()
    if not shelve:
        shelve = Shelve(
            name="메인 카운터 매대",
            store_id=store.id,
            terminal_id="TERM-8888",
            business_number="888-88-88888",
            vender_code="VEND-8888"
        )
        db.add(shelve)
        db.commit()
        db.refresh(shelve)

    # 6. 카테고리 보장 (추천 요리, 식사류, 음료/주류)
    categories_data = [
        {"name": "🔥 추천 요리", "sequence": 1},
        {"name": "🍚 식사류", "sequence": 2},
        {"name": "🥤 음료/주류", "sequence": 3}
    ]
    
    categories = {}
    for cat_info in categories_data:
        stmt = select(Category).where(Category.name == cat_info["name"], Category.store_id == store.id)
        cat = db.execute(stmt).scalars().first()
        if not cat:
            cat = Category(
                name=cat_info["name"],
                sequence=cat_info["sequence"],
                shelve_id=shelve.id,
                store_id=store.id
            )
            db.add(cat)
            db.commit()
            db.refresh(cat)
        categories[cat_info["name"]] = cat

    # 7. 상품 보장 (오프라인 더미 데이터와 동일한 구성으로 연동)
    products_data = [
        # 추천 요리
        {"category": "🔥 추천 요리", "name": "명품 짜장면", "price": 7000, "stock": 50, "status": "ACTIVE", "sequence": 1},
        {"category": "🔥 추천 요리", "name": "해물 짬뽕", "price": 8500, "stock": 20, "status": "ACTIVE", "sequence": 2},
        {"category": "🔥 추천 요리", "name": "찹쌀 탕수육 (소)", "price": 15000, "stock": 10, "status": "ACTIVE", "sequence": 3},
        {"category": "🔥 추천 요리", "name": "군만두 (8개)", "price": 6000, "stock": 0, "status": "SOLDOUT", "sequence": 4},
        # 식사류
        {"category": "🍚 식사류", "name": "볶음밥", "price": 8000, "stock": 30, "status": "ACTIVE", "sequence": 1},
        {"category": "🍚 식사류", "name": "잡채밥", "price": 9000, "stock": 15, "status": "ACTIVE", "sequence": 2},
        # 음료/주류
        {"category": "🥤 음료/주류", "name": "콜라", "price": 2000, "stock": 100, "status": "ACTIVE", "sequence": 1},
        {"category": "🥤 음료/주류", "name": "사이다", "price": 2000, "stock": 100, "status": "ACTIVE", "sequence": 2}
    ]

    for prod_info in products_data:
        stmt = select(Product).where(Product.name == prod_info["name"], Product.store_id == store.id)
        prod = db.execute(stmt).scalars().first()
        if not prod:
            cat = categories[prod_info["category"]]
            prod = Product(
                category_id=cat.id,
                store_id=store.id,
                shelve_id=shelve.id,
                kiosk_id=kiosk.id,
                name=prod_info["name"],
                price=prod_info["price"],
                stock=prod_info["stock"],
                image="", # 필수 필드 (Not Null) 채워주기
                stock_managed=True, # 재고 관리 켜기
                sequence=prod_info["sequence"],
                is_active=True if prod_info["status"] == "ACTIVE" else False
            )
            # 만약 품절 상품이라면, API 정합성을 위해 수량을 0으로 매핑
            if prod_info["status"] == "SOLDOUT":
                prod.stock = 0
            db.add(prod)
            
    db.commit()
