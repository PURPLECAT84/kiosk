import sys
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import engine, DB_session, Base
from models.user import User
from models.store import Store
from models.shelve import Shelve
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem
from core.security import get_password_hash

fake = Faker('ko_KR')

# 1. Base Product Data
PRODUCT_BASE_DATA = [
    # 스낵류
    ("새우깡", "스낵", 1500), ("포카칩", "스낵", 1700), ("양파링", "스낵", 1500),
    ("꿀꽈배기", "스낵", 1500), ("오징어땅콩", "스낵", 2000), ("홈런볼", "스낵", 1800),
    ("맛동산", "스낵", 2000), ("꼬깔콘", "스낵", 1500), ("바나나킥", "스낵", 1500),
    ("자갈치", "스낵", 1500), ("치토스", "스낵", 1500), ("감자깡", "스낵", 1500),
    ("죠리퐁", "스낵", 1500), ("초코파이", "스낵", 4800), ("몽쉘", "스낵", 5000),
    ("오예스", "스낵", 4500), ("마가렛트", "스낵", 4400), ("쿠크다스", "스낵", 3000),
    ("버터와플", "스낵", 3500), ("카스타드", "스낵", 4400), ("다이제", "스낵", 2500),
    ("스윙칩", "스낵", 1700), ("눈을감자", "스낵", 2000), ("오감자", "스낵", 1500),
    ("허니버터칩", "스낵", 1700),
    # 음료류
    ("코카콜라", "음료", 2000), ("칠성사이다", "음료", 1800), ("환타 오렌지", "음료", 1500),
    ("조지아 오리지널", "음료", 1200), ("레쓰비", "음료", 1000), ("칸타타", "음료", 2500),
    ("비타500", "음료", 1000), ("박카스D", "음료", 900), ("오로나민C", "음료", 1200),
    ("포카리스웨트", "음료", 2000), ("토레타", "음료", 2000), ("게토레이", "음료", 1800),
    ("파워에이드", "음료", 2200), ("몬스터 에너지", "음료", 2500), ("핫식스", "음료", 1500),
    ("레드불", "음료", 3000), ("펩시제로", "음료", 1800), ("코카콜라제로", "음료", 2000),
    ("밀키스", "음료", 1500), ("데미소다", "음료", 1200), ("이프로", "음료", 1500),
    ("옥수수수염차", "음료", 1500), ("헛개수", "음료", 2000), ("보리차", "음료", 1500),
    ("삼다수 500ml", "음료", 1000), ("에비앙 500ml", "음료", 1500),
    # 컵라면/가공식품
    ("신라면 컵", "컵라면", 1400), ("진라면 매운맛 컵", "컵라면", 1200), ("진라면 순한맛 컵", "컵라면", 1200),
    ("육개장 사발면", "컵라면", 1000), ("팔도비빔면 컵", "컵라면", 1500), ("짜파게티 범벅", "컵라면", 1000),
    ("참깨라면 컵", "컵라면", 1500), ("새우탕 컵", "컵라면", 1400), ("튀김우동 컵", "컵라면", 1400),
    ("블랙신라면 컵", "컵라면", 1800), ("불닭볶음면 컵", "컵라면", 1600), ("오징어짬뽕 컵", "컵라면", 1500),
    ("도시락", "컵라면", 1000), ("왕뚜껑", "컵라면", 1400), ("김치사발면", "컵라면", 1000),
    ("햇반 210g", "가공식품", 1800), ("스팸 200g", "가공식품", 4500), ("참치캔 150g", "가공식품", 3500),
    ("3분카레", "가공식품", 2000), ("3분짜장", "가공식품", 2000), ("맛밤", "가공식품", 3500),
    # 아이스크림
    ("메로나", "아이스크림", 1200), ("비비빅", "아이스크림", 1200), ("죠스바", "아이스크림", 1200),
    ("스크류바", "아이스크림", 1200), ("수박바", "아이스크림", 1200), ("쌍쌍바", "아이스크림", 1200),
    ("돼지바", "아이스크림", 1200), ("바밤바", "아이스크림", 1200), ("누가바", "아이스크림", 1200),
    ("투게더", "아이스크림", 7000), ("붕어싸만코", "아이스크림", 2000), ("월드콘", "아이스크림", 2000),
    ("부라보콘", "아이스크림", 2000), ("구구콘", "아이스크림", 2000), ("설레임", "아이스크림", 1500),
    ("더위사냥", "아이스크림", 1500), ("빠삐코", "아이스크림", 1200), ("탱크보이", "아이스크림", 1200),
    # 신선식품(간편식)
    ("참치마요 삼각김밥", "간편식", 1200), ("전주비빔 삼각김밥", "간편식", 1300), ("스팸김치 삼각김밥", "간편식", 1300),
    ("치킨너겟 삼각", "간편식", 1500), ("제육볶음 도시락", "간편식", 4500), ("돈까스 도시락", "간편식", 5000),
    ("치킨마요 도시락", "간편식", 4800), ("햄치즈 샌드위치", "간편식", 2500), ("에그스프레드 샌드위치", "간편식", 2800),
    ("불고기버거", "간편식", 3000), ("치킨버거", "간편식", 3200), ("핫도그", "간편식", 2000),
    ("구운계란 2구", "간편식", 2200), ("스트링치즈", "간편식", 1500), ("맥스봉", "간편식", 2000),
    ("천하장사", "간편식", 1800), ("훈제닭가슴살", "간편식", 3500),
    # 생필품
    ("물티슈 100매", "생필품", 2000), ("두루마리휴지 1롤", "생필품", 1000), ("여행용티슈", "생필품", 800),
    ("샴푸 린스 세트 미니", "생필품", 4000), ("칫솔 1개", "생필품", 1500), ("치약 50g", "생필품", 1500),
    ("비누 1알", "생필품", 1200), ("바디워시 미니", "생필품", 2500), ("면도기", "생필품", 2000),
    ("생리대 중형", "생필품", 4000), ("스타킹", "생필품", 3500), ("건전지 AA 2알", "생필품", 3000),
    ("건전지 AAA 2알", "생필품", 3000), ("라이터", "생필품", 800), ("우산", "생필품", 6000),
    ("우의", "생필품", 4000), ("일회용 마스크 5매", "생필품", 3000), ("밴드 10매", "생필품", 1500),
    ("마데카솔", "생필품", 6000), ("종이컵 1줄", "생필품", 1500), ("나무젓가락 10팩", "생필품", 1000)
]

def main():
    print("🚀 데이터 생성을 시작합니다...")
    
    # DB 테이블 생성 방치
    Base.metadata.create_all(bind=engine)
    
    db: Session = DB_session()
    try:
        print(">> 패스워드 '1111' 해싱 중...")
        common_password = get_password_hash("1111")
        
        # 1. User 30명 생성
        print(">> User 30명 생성 중...")
        users = []
        user_roles = ["company"] * 6 + ["owner"] * 12 + ["manager"] * 12
        random.shuffle(user_roles)
        
        for i, role in enumerate(user_roles):
            email = f"{role}{i+1}@test.com"
            stmt = select(User).where(User.email == email)
            existing_user = db.scalars(stmt).first()
            if existing_user:
                users.append(existing_user)
                continue
                
            new_user = User(
                email=email,
                password=common_password,
                name=fake.name(),
                phone=fake.phone_number(),
                address=fake.address(),
                authority=role,
                joined_date=fake.date_time_between(start_date="-1y", end_date="now")
            )
            db.add(new_user)
            users.append(new_user)
        
        db.commit()
        for u in users:
            db.refresh(u)
        print(f"✅ User 30명 정상 확인 (총 {len(users)}명 가용)")
        
        # 2. Store 50개 생성
        print(">> Store 50개 생성 중...")
        stores = []
        store_types = ["convenience", "cafe", "restaurant", "retail"]
        target_stores = 50
        
        # 이미 있는 더미 매장이 있는지 확인
        stmt = select(Store).where(Store.name.contains("점"))
        existing_stores = db.scalars(stmt).all()
        stores.extend(existing_stores)
        
        for i in range(target_stores - len(existing_stores)):
            user = random.choice(users) 
            store_name = f"{fake.company()} {fake.city()}점"
            
            stmt = select(Store).where(Store.name == store_name)
            if db.scalars(stmt).first():
                continue
            
            store = Store(
                user_id=user.id,
                type=random.choice(store_types),
                name=store_name,
                address=fake.address(),
                created_date=fake.date_time_between(start_date="-1y", end_date="now")
            )
            db.add(store)
            stores.append(store)
            
        db.commit()
        for s in stores: db.refresh(s)
        print(f"✅ Store {len(stores)}개 확보 완료")
        
        # 3. 매장당 Shelve, Category, Product 할당
        print(">> 매대, 카테고리, 상품 데이터 생성 중...")
        # 상품이 하나도 없는 매장에만 생성하도록 필터링 (중복 실행 방지)
        for store in stores:
            stmt = select(Product).where(Product.store_id == store.id).limit(1)
            if db.scalars(stmt).first():
                continue # 이미 상품이 추가된 매장 패스
                
            for sh_idx in range(random.randint(1, 2)):
                TerminalString = f"T_{fake.ean8()}"
                shelve = Shelve(
                    store_id=store.id,
                    name=f"매대-{sh_idx+1}",
                    terminal_id=TerminalString[:20],
                    business_number=fake.numerify("###-##-#####"),
                    vender_code=fake.bothify("V_####")
                )
                db.add(shelve)
                db.flush() 
                
                cats = random.sample(list(set([p[1] for p in PRODUCT_BASE_DATA])), random.randint(2, 4))
                
                for cat_name in cats:
                    category = Category(
                        shelve_id=shelve.id,
                        store_id=store.id,
                        name=cat_name
                    )
                    db.add(category)
                    db.flush()
                    
                    matched_products = [p for p in PRODUCT_BASE_DATA if p[1] == cat_name]
                    selected_prods = random.sample(matched_products, k=min(len(matched_products), random.randint(3, 8)))
                    
                    for prod in selected_prods:
                        product = Product(
                            category_id=category.id,
                            store_id=store.id,
                            shelve_id=shelve.id,
                            barcode=fake.ean13(),
                            name=prod[0],
                            price=prod[2],
                            buy_from="본사물류",
                            image="https://via.placeholder.com/150", 
                            stock=random.randint(50, 200),
                            is_active=True
                        )
                        db.add(product)
            db.commit()
        
        print("✅ 매대, 카테고리, 상품 데이터 생성 완료")
        
        # 4. Order & OrderItem 생성
        print(">> 시작일~종료일 주문 데이터 생성 중... 시간이 조금 걸립니다 ⏳")
        start_date = datetime(2026, 1, 1)
        end_date = datetime(2026, 3, 31)
        delta_days = (end_date - start_date).days
        
        payment_methods = ["Card", "Cash", "EasyPay", "GiftCard"]
        payment_providers = ["Toss", "KakaoPay", "NaverPay", "SamsungPay", "Nice"]
        
        total_orders_created = 0
        
        # 각 매장당 주문이 없으면 생성
        for store in stores:
            stmt = select(Order).where(Order.store_id == store.id).limit(1)
            if db.scalars(stmt).first():
                continue # 이미 주문이 생성된 매장은 패스
                
            stmt = select(Product).where(Product.store_id == store.id)
            store_products = db.scalars(stmt).all()
            
            if not store_products: 
                continue
                
            num_orders = random.randint(80, 120)
            
            for _ in range(num_orders):
                random_days = random.randint(0, delta_days)
                random_seconds = random.randint(0, 86400)
                order_date = start_date + timedelta(days=random_days, seconds=random_seconds)
                
                chosen_prods = random.sample(store_products, k=random.randint(1, min(5, len(store_products))))
                
                items_data = []
                total_amount = 0
                for cp in chosen_prods:
                    qty = random.randint(1, 3)
                    items_data.append((cp, qty))
                    total_amount += (cp.price * qty)
                    
                order = Order(
                    store_id=store.id,
                    total_amount=total_amount,
                    payment_method=random.choice(payment_methods),
                    payment_provider=random.choice(payment_providers),
                    approval_code=fake.bothify("AUTH_########"),
                    status="Completed",
                    created_date=order_date
                )
                
                for cp, qty in items_data:
                    order_item = OrderItem(
                        product_id=cp.id,
                        product_name=cp.name,
                        product_price=cp.price,
                        quantity=qty
                    )
                    order.items.append(order_item)
                
                db.add(order)
                total_orders_created += 1
            
            if (stores.index(store) + 1) % 5 == 0:
                print(f"   [{stores.index(store) + 1}/{len(stores)}] 매장 (총 {total_orders_created}건 생성중...)")
                db.commit()
        
        db.commit()
        print(f"✅ 주문 데이터 {total_orders_created}건 생성 완료")
        print("🎉 모든 더미데이터 생성이 성공적으로 끝났습니다!")
        
    except Exception as e:
        print(f"❌ 데이터 생성 중 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
