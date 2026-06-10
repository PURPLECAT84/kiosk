# PM/Scripts/qc_integration_test.py
import sys
import os
import time
import subprocess
import httpx
import uuid

# Backend 폴더를 Python 경로에 추가하여 모듈을 임포트할 수 있도록 설정
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backend'))

from database import DB_session
from models.user import UserInfo, UserRole, UserStatus, BusinessInfo
from models.store import Store
from models.kiosk import Kiosk
from models.kiosk_admin import KioskAdmin
from models.shelve import Shelve
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem

BASE_URL = "http://127.0.0.1:8001"

def clean_database(owner_email, dev_email, helper_email=None):
    """테스트용으로 적재된 모든 임시 레코드를 데이터베이스에서 물리적으로 완벽히 지웁니다."""
    db = DB_session()
    try:
        # 이메일로 사용자 조회
        owner = db.query(UserInfo).filter(UserInfo.email == owner_email).first()
        dev = db.query(UserInfo).filter(UserInfo.email == dev_email).first()
        helper = db.query(UserInfo).filter(UserInfo.email == helper_email).first() if helper_email else None
        
        user_ids = []
        if owner: user_ids.append(owner.id)
        if dev: user_ids.append(dev.id)
        if helper: user_ids.append(helper.id)
        
        if user_ids:
            # 1. KioskAdmin 삭제
            db.query(KioskAdmin).filter(KioskAdmin.user_id.in_(user_ids)).delete(synchronize_session=False)
            
            # 2. Store 및 소유 상품, 카테고리, 매대, 주문서 삭제
            stores = db.query(Store).filter(Store.user_id.in_(user_ids)).all()
            store_ids = [s.id for s in stores]
            if store_ids:
                # 주문 아이템 및 주문서 삭제
                orders = db.query(Order).filter(Order.store_id.in_(store_ids)).all()
                order_ids = [o.id for o in orders]
                if order_ids:
                    db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
                    db.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
                
                # 상품 삭제
                db.query(Product).filter(Product.kiosk_id.in_(
                    db.query(Kiosk.id).filter(Kiosk.store_id.in_(store_ids))
                )).delete(synchronize_session=False)
                
                # 카테고리 삭제
                db.query(Category).filter(Category.store_id.in_(store_ids)).delete(synchronize_session=False)
                
                # 매대 삭제
                db.query(Shelve).filter(Shelve.store_id.in_(store_ids)).delete(synchronize_session=False)
                
                # 키오스크 삭제
                db.query(Kiosk).filter(Kiosk.store_id.in_(store_ids)).delete(synchronize_session=False)
                
                # 매장 삭제
                db.query(Store).filter(Store.id.in_(store_ids)).delete(synchronize_session=False)
                
            # 3. 비즈니스 정보 삭제
            db.query(BusinessInfo).filter(BusinessInfo.user_id.in_(user_ids)).delete(synchronize_session=False)
            
            # 4. 유저 삭제
            db.query(UserInfo).filter(UserInfo.id.in_(user_ids)).delete(synchronize_session=False)
            
            db.commit()
            print("🧹 [CLEANUP] 이전 테스트 더미 데이터를 성공적으로 삭제했습니다.")
    except Exception as e:
        db.rollback()
        print(f"⚠️ [CLEANUP ERROR] 클리업 중 오류 발생: {e}")
    finally:
        db.close()

def run_tests():
    owner_email = "qc_owner@moki.com"
    dev_email = "qc_dev@moki.com"
    helper_email = "qc_helper@moki.com"
    password = "Password123!"

    # 0. 이전 테스트 데이터 사전 삭제
    clean_database(owner_email, dev_email, helper_email)

    # 1. 백엔드 테스트 서버 구동 (포트 8001)
    print("🚀 [TEST SERVER] FastAPI 테스트 서버 연결 시작 (포트 8001)...")

    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    try:
        # 2. 회원가입 및 DB 권한 세팅
        print("\n--- 1. 회원가입 및 권한 승인 검증 ---")
        
        # 사장님 회원가입
        res = client.post("/users/signup", json={
            "email": owner_email,
            "password": password,
            "name": "QC점주",
            "phone": "010-1111-2222"
        })
        assert res.status_code == 201, f"사장님 회원가입 실패: {res.text}"
        owner_id = res.json()["id"]
        print("✅ 사장님 회원가입 완료")

        # 개발자 회원가입
        res = client.post("/users/signup", json={
            "email": dev_email,
            "password": password,
            "name": "QC개발자",
            "phone": "010-3333-4444"
        })
        assert res.status_code == 201, f"개발자 회원가입 실패: {res.text}"
        dev_id = res.json()["id"]
        print("✅ 개발자 회원가입 완료")

        # 도우미 회원가입 (키오스크 부관리자 테스트용)
        res = client.post("/users/signup", json={
            "email": helper_email,
            "password": password,
            "name": "QC도우미",
            "phone": "010-5555-6666"
        })
        assert res.status_code == 201, f"도우미 회원가입 실패: {res.text}"
        helper_id = res.json()["id"]
        print("✅ 도우미 회원가입 완료")

        # 개발자 계정의 Role을 DEV로 수동 변경 (DB 직접 수정)
        db = DB_session()
        dev_user = db.get(UserInfo, uuid.UUID(dev_id))
        dev_user.role = UserRole.DEV
        dev_user.status = UserStatus.ACTIVE
        
        # 도우미 계정도 활성 상태로 변경
        helper_user = db.get(UserInfo, uuid.UUID(helper_id))
        helper_user.status = UserStatus.ACTIVE
        
        db.commit()
        db.close()
        print("✅ DB 직접 업데이트를 통한 개발자(DEV) 권한 부여 및 도우미 활성화 완료")

        # 3. 로그인 및 JWT 토큰 획득
        print("\n--- 2. JWT 로그인 인증 및 출입증 획득 ---")
        
        # 사장님 로그인
        res = client.post("/users/login", data={"username": owner_email, "password": password})
        assert res.status_code == 200, f"사장님 로그인 실패: {res.text}"
        owner_token = res.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print("✅ 사장님 로그인 및 토큰 확인 완료")

        # 개발자 로그인
        res = client.post("/users/login", data={"username": dev_email, "password": password})
        assert res.status_code == 200, f"개발자 로그인 실패: {res.text}"
        dev_token = res.json()["access_token"]
        dev_headers = {"Authorization": f"Bearer {dev_token}"}
        print("✅ 개발자 로그인 및 토큰 확인 완료")

        # 4. 사업자 정보 등록 & DEV 관리자 자격 심사
        print("\n--- 3. 사업자 정보 등록 및 매장 자동 생성 검증 ---")
        
        res = client.post("/users/me/business", headers=owner_headers, json={
            "business_number": "999-99-99999",
            "business_name": "QC모키가게",
            "representative_name": "QC점주",
            "representative_phone": "010-1111-2222",
            "store_name": "QC가맹매장",
            "document_url": "/static/images/qc_doc.png"
        })
        assert res.status_code == 200, f"사업자 정보 추가 실패: {res.text}"
        print("✅ 사장님 사업자 서류 등록 요청 성공 (Store 가상 생성 완료)")

        # 개발자가 점주 자격 승인 토글 처리
        res = client.patch(f"/users/{owner_id}/verify-business", headers=dev_headers, params={"is_verified": True})
        assert res.status_code == 200, f"사업자 승인 실패: {res.text}"
        assert res.json()["is_business_verified"] is True, "사업자 확인 플래그 미갱신"
        print("✅ DEV 권한 관리자에 의한 사업자 승인 완료 (is_business_verified=True)")

        # 5. 매장 조회 및 키오스크 기기 등록
        print("\n--- 4. 인증완료 매장 조회 및 키오스크 등록 검증 ---")
        
        res = client.get("/kiosks/active-stores", headers=owner_headers)
        assert res.status_code == 200, f"액티브 매장 목록 조회 실패: {res.text}"
        stores_data = res.json()
        assert len(stores_data) > 0, "인증 완료 매장이 반환되지 않았습니다."
        store_id = stores_data[0]["id"]
        print(f"✅ 인증 완료 매장 조회 성공 (매장명: {stores_data[0]['name']}, ID: {store_id})")

        # 키오스크 등록
        res = client.post("/kiosks/", headers=owner_headers, json={
            "name": "QC주문기01",
            "model_name": "K-MOKI-QC",
            "type": "Restaurant",
            "status": "WAITING",
            "store_id": store_id
        })
        assert res.status_code == 201, f"키오스크 등록 실패: {res.text}"
        kiosk_id = res.json()["id"]
        kiosk_code = res.json()["code"]
        assert kiosk_code.startswith("KS"), "키오스크 코드는 KS로 시작해야 합니다."
        print(f"✅ 키오스크 기기 성공 등록 (기기 ID: {kiosk_id}, 코드: {kiosk_code})")

        # 내가 관리하는 기기 리스트 조회
        res = client.get("/kiosks/my", headers=owner_headers)
        assert res.status_code == 200, f"내 기기 목록 조회 실패: {res.text}"
        my_kiosks = res.json()
        assert any(k["id"] == kiosk_id for k in my_kiosks), "생성된 키오스크가 내 권한 목록에 존재하지 않습니다."
        print("✅ 내가 관리하는 키오스크 권한 자동 매핑(KioskAdmin) 검증 완료")

        # 6. 매대(Shelve) 및 카테고리, 상품 구성
        print("\n--- 5. 매장 카탈로그 (매대, 카테고리, 상품) 빌드 검증 ---")
        
        # 6-1. 매대 생성
        res = client.post(f"/shelves/store/{store_id}/shelve", headers=owner_headers, json={
            "name": "QC기본진열대",
            "terminal_id": "T001",
            "business_number": "999-99-99999",
            "vender_code": "V001"
        })
        assert res.status_code == 201, f"매대 생성 실패: {res.text}"
        shelve_id = res.json()["id"]
        print(f"✅ 매대 생성 성공 (ID: {shelve_id})")

        # 6-2. 카테고리 생성
        res = client.post("/categories/", headers=owner_headers, json={
            "name": "QC짜장짬뽕류",
            "shelve_id": shelve_id
        })
        assert res.status_code == 201, f"카테고리 생성 실패: {res.text}"
        category_id = res.json()["id"]
        print(f"✅ 카테고리 생성 성공 (ID: {category_id})")

        # 6-3. 상품 등록 및 특정 키오스크 귀속
        res = client.post("/products/", headers=owner_headers, json={
            "category_id": category_id,
            "name": "QC수제짜장",
            "price": 6500,
            "buy_from": "모키푸드",
            "image": "/static/images/jjajang.png",
            "stock": 5,
            "stock_managed": True,
            "kiosk_id": kiosk_id
        })
        assert res.status_code == 201, f"상품 등록 실패: {res.text}"
        product_id = res.json()["id"]
        print(f"✅ 상품 생성 및 기기 귀속 성공 (상품: QC수제짜장, ID: {product_id})")

        # 7. 키오스크 클라이언트 동기화 & 가상 결제
        print("\n--- 6. 키오스크 클라이언트 연동 및 주문 처리 검증 ---")
        
        # 키오스크 클라이언트 기기동기화 API
        res = client.get(f"/kiosk_client/sync/{kiosk_id}")
        assert res.status_code == 200, f"클라이언트 동기화 API 실패: {res.text}"
        sync_data = res.json()
        assert sync_data["store_name"] == "QC가맹매장", "매장명이 일치하지 않습니다."
        assert sync_data["kiosk_type"] == "Restaurant", "기기 유형이 일치하지 않습니다."
        assert len(sync_data["categories"]) > 0, "카테고리가 노출되지 않습니다."
        assert sync_data["categories"][0]["products"][0]["name"] == "QC수제짜장", "귀속된 상품이 노출되지 않습니다."
        print("✅ Kiosk Client 동기화 데이터 정합성 확인 완료")

        # 가상 주문 결제 요청
        res = client.post("/kiosk_client/pay/mock", json={
            "store_id": store_id,
            "kiosk_id": kiosk_id,
            "total_amount": 6500,
            "payment_method": "카드",
            "order_no": "010-9876-5432",
            "items": [
                {"product_id": product_id, "quantity": 1}
            ]
        })
        assert res.status_code == 200, f"가상 결제 처리 실패: {res.text}"
        order_no = res.json()["order_no"]
        print(f"✅ 가상 결제 처리 및 주문 적재 완료 (주문번호: {order_no})")

        # 재고 수량 확인 (5개에서 4개로 줄어들었는지 검증)
        res = client.get(f"/kiosk_client/sync/{kiosk_id}")
        current_stock = res.json()["categories"][0]["products"][0]["stock"]
        assert current_stock == 4, f"재고 차감이 정상 동작하지 않았습니다: {current_stock}개"
        print("✅ Mock 결제에 따른 상품 재고 실시간 차감 검증 완료")

        # 8. 글로벌 기기 필터 헤더 검증 (X-Kiosk-Id)
        print("\n--- 7. 글로벌 기기 필터 헤더(X-Kiosk-Id) 작동 검증 ---")
        
        # 8-1. 대시보드 통계 조회 검증
        # 활성 키오스크 헤더 주입 시
        res = client.get("/dashboard/summary", headers={**owner_headers, "X-Kiosk-Id": kiosk_id})
        assert res.status_code == 200, f"통계 조회 실패: {res.text}"
        assert res.json()["today_sales"] == 6500, "오늘의 매출이 계산되지 않았습니다."
        print(f"✅ X-Kiosk-Id 주입 통계: {res.json()['today_sales']}원 (기기 귀속 매출 필터링 성공)")

        # 존재하지 않는 임의의 기기 ID 주입 시 -> 0원 반환되어야 함
        fake_kiosk_id = str(uuid.uuid4())
        res = client.get("/dashboard/summary", headers={**owner_headers, "X-Kiosk-Id": fake_kiosk_id})
        assert res.json()["today_sales"] == 0, f"임의 기기 헤더 주입에도 매출이 필터링되지 않았습니다: {res.json()['today_sales']}원"
        print("✅ 존재하지 않는 X-Kiosk-Id 주입 통계: 0원 (기기 격리 필터 작동 정상)")

        # 8-2. 주문 내역 조회 검증
        # 활성 키오스크 헤더 주입 시 -> 1건의 주문이 리턴되어야 함
        res = client.get(f"/order/?store_id={store_id}", headers={**owner_headers, "X-Kiosk-Id": kiosk_id})
        assert res.status_code == 200, f"주문 목록 조회 실패: {res.text}"
        assert len(res.json()) == 1, f"기기에 귀속된 주문이 조회되지 않았습니다. 건수: {len(res.json())}"
        print("✅ X-Kiosk-Id 주입 주문 내역: 1건 조회 성공")

        # 임의의 기기 ID 주입 시 -> 0건 리턴되어야 함
        res = client.get(f"/order/?store_id={store_id}", headers={**owner_headers, "X-Kiosk-Id": fake_kiosk_id})
        assert len(res.json()) == 0, f"주문 목록이 기기 ID 기준으로 필터링되지 않았습니다: {len(res.json())}건"
        print("✅ 존재하지 않는 X-Kiosk-Id 주입 주문 내역: 0건 (주문 격리 필터 작동 정상)")

        # 9. 기기 다중 관리자 매핑 관리 (KioskAdmin) 검증
        print("\n--- 8. 키오스크 다중 관리자(KioskAdmin) 매핑 권한 검증 ---")
        
        # 관리자 목록 조회
        res = client.get(f"/kiosks/{kiosk_id}/admins", headers=owner_headers)
        assert res.status_code == 200, f"관리자 리스트 조회 실패: {res.text}"
        admins_list = res.json()
        assert len(admins_list) == 1, "최초 소유자 1명만 있어야 함"
        assert admins_list[0]["role"] == "MASTER", "점주는 MASTER 권한이어야 함"
        print("✅ 최초 등록 점주의 MASTER 권한 확인 완료")

        # 신규 도우미 추가
        res = client.post(f"/kiosks/{kiosk_id}/admins", headers=owner_headers, json={
            "email": helper_email,
            "role": "STAFF"
        })
        assert res.status_code == 200, f"관리자 추가 실패: {res.text}"
        print("✅ 신규 도우미를 STAFF 권한으로 성공 추가")

        # 추가된 관리자 권한 수정 (STAFF -> MANAGER)
        res = client.patch(f"/kiosks/{kiosk_id}/admins/{helper_id}", headers=owner_headers, json={
            "role": "MANAGER"
        })
        assert res.status_code == 200, f"관리자 권한 변경 실패: {res.text}"
        assert res.json()["role"] == "MANAGER", "역할 수정 미반영"
        print("✅ 추가된 도우미의 권한 수정(STAFF -> MANAGER) 성공")

        # 관리자 목록에서 제거
        res = client.delete(f"/kiosks/{kiosk_id}/admins/{helper_id}", headers=owner_headers)
        assert res.status_code == 204, f"관리자 해제 실패: {res.text}"
        
        # 최종 확인
        res = client.get(f"/kiosks/{kiosk_id}/admins", headers=owner_headers)
        assert len(res.json()) == 1, "관리자가 정상적으로 제거되지 않았습니다."
        print("✅ 도우미 권한 해제 및 목록 복구 확인 완료")

        print("\n==============================================")
        print("🎉 [ALL TESTS PASSED] E2E 통합 테스트 전체 통과!")
        print("==============================================")

    except Exception as e:
        print(f"\n❌ [TEST FAILED] 테스트 진행 도중 검증 에러 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        # 10. 테스트 적재 데이터 깔끔하게 제거 (DB 청소)
        clean_database(owner_email, dev_email, helper_email)
        print("🛑 [TEST SERVER] 테스트 완료.")

if __name__ == "__main__":
    run_tests()
