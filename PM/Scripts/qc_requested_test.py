# PM/Scripts/qc_requested_test.py
import sys
import os
import httpx
import uuid
import random
from datetime import datetime

# Backend 폴더를 Python 경로에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Backend'))

from database import DB_session
from models.user import UserInfo, UserRole, UserStatus, BusinessInfo
from models.kiosk import Kiosk
from models.kiosk_admin import KioskAdmin
from models.shelve import Shelve
from models.category import Category
from models.product import Product
from models.order import Order
from models.order_item import OrderItem

BASE_URL = "http://127.0.0.1:8000"

def clean_database(owner_email, dev_email):
    """테스트 계정과 관련된 모든 데이터를 청소합니다."""
    db = DB_session()
    try:
        owner = db.query(UserInfo).filter(UserInfo.email == owner_email).first()
        dev = db.query(UserInfo).filter(UserInfo.email == dev_email).first()
        
        user_ids = []
        if owner: user_ids.append(owner.id)
        if dev: user_ids.append(dev.id)
        
        if user_ids:
            db.query(KioskAdmin).filter(KioskAdmin.user_id.in_(user_ids)).delete(synchronize_session=False)
            
            kiosks = db.query(Kiosk).filter(Kiosk.user_id.in_(user_ids)).all()
            kiosk_ids = [k.id for k in kiosks]
            
            # DEV 계정 소유의 키오스크 및 관리 기기도 삭제 대상에 포함하기 위해 추가 조회
            all_admins = db.query(KioskAdmin).all()
            kiosk_ids_extended = list(kiosk_ids)
            for ka in all_admins:
                if ka.user_id in user_ids and ka.kiosk_id not in kiosk_ids_extended:
                    kiosk_ids_extended.append(ka.kiosk_id)
            
            if kiosk_ids_extended:
                orders = db.query(Order).filter(Order.kiosk_id.in_(kiosk_ids_extended)).all()
                order_ids = [o.id for o in orders]
                if order_ids:
                    db.query(OrderItem).filter(OrderItem.order_id.in_(order_ids)).delete(synchronize_session=False)
                    db.query(Order).filter(Order.id.in_(order_ids)).delete(synchronize_session=False)
                
                db.query(Product).filter(Product.kiosk_id.in_(kiosk_ids_extended)).delete(synchronize_session=False)
                db.query(Category).filter(Category.kiosk_id.in_(kiosk_ids_extended)).delete(synchronize_session=False)
                db.query(Shelve).filter(Shelve.kiosk_id.in_(kiosk_ids_extended)).delete(synchronize_session=False)
                db.query(Kiosk).filter(Kiosk.id.in_(kiosk_ids_extended)).delete(synchronize_session=False)
                
            db.query(BusinessInfo).filter(BusinessInfo.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(UserInfo).filter(UserInfo.id.in_(user_ids)).delete(synchronize_session=False)
            db.commit()
            print("[CLEANUP] 이전 요청 테스트 더미 데이터를 정리 완료했습니다.")
    except Exception as e:
        db.rollback()
        print(f"[CLEANUP ERROR] 클린업 중 오류: {e}")
    finally:
        db.close()

def run_requested_test():
    owner_email = "req_owner@moki.com"
    dev_email = "req_dev@moki.com"
    password = "Password123!"

    # 0. 이전 데이터 청소
    clean_database(owner_email, dev_email)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    try:
        print("\n==============================================")
        print("[QC TEST START] 요청 결제 및 실명인증 시나리오 구동")
        print("==============================================")

        # 1. 회원가입
        print("\n--- [Step 1] 신규 회원 가입 ---")
        # 1-1. 점주 회원가입
        res = client.post("/users/signup", json={
            "email": owner_email,
            "password": password,
            "name": "요청점주",
            "phone": "010-1234-5678"
        })
        assert res.status_code == 201, f"점주 가입 실패: {res.text}"
        owner_id = res.json()["id"]
        print(f"[OK] 점주 가입 성공 (ID: {owner_id})")

        # 1-2. DEV용 가상 계정 회원가입
        res = client.post("/users/signup", json={
            "email": dev_email,
            "password": password,
            "name": "요청DEV",
            "phone": "010-9999-8888"
        })
        assert res.status_code == 201, f"DEV 가입 실패: {res.text}"
        dev_id = res.json()["id"]
        print(f"[OK] DEV 가입 성공 (ID: {dev_id})")

        # DB 권한 직접 조율 (DEV 계정 상태를 DEV 및 ACTIVE로 변경)
        db = DB_session()
        dev_user = db.get(UserInfo, uuid.UUID(dev_id))
        dev_user.role = UserRole.DEV
        dev_user.status = UserStatus.ACTIVE
        
        # 점주 상태도 일단 ACTIVE로 변경
        owner_user = db.get(UserInfo, uuid.UUID(owner_id))
        owner_user.status = UserStatus.ACTIVE
        db.commit()
        db.close()
        print("[OK] DB 직접 업데이트를 통한 가상 역할(DEV) 승인")

        # 2. 로그인 수행
        print("\n--- [Step 2] 로그인 및 JWT 획득 ---")
        res = client.post("/users/login", data={"username": owner_email, "password": password})
        owner_token = res.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}
        print("[OK] 점주 JWT 로그인 성공")

        res = client.post("/users/login", data={"username": dev_email, "password": password})
        dev_token = res.json()["access_token"]
        dev_headers = {"Authorization": f"Bearer {dev_token}"}
        print("[OK] DEV 계정 JWT 로그인 성공")

        # 3. 실명 인증 (인라인 SMS OTP 모킹 연동 검증)
        print("\n--- [Step 3] 신규 가입자 휴대폰 실명인증 검증 ---")
        res = client.post("/auth/identity-verification/send", headers=owner_headers, json={
            "name": "요청점주",
            "phone": "01012345678",
            "operator": "SKT",
            "birth_date": "19900101",
            "gender": "MALE"
        })
        assert res.status_code == 200, f"SMS 인증번호 발송 요청 실패: {res.text}"
        verification_id = res.json()["verification_id"]
        print(f"[OK] 본인인증 발송 성공 (verification_id: {verification_id})")

        # OTP 검증 확인 호출
        res = client.post("/auth/identity-verification/confirm", headers=owner_headers, json={
            "verification_id": verification_id,
            "otp": "000000" # 모의 승인 번호
        })
        assert res.status_code == 200, f"본인인증 승인 실패: {res.text}"
        print(f"[OK] 본인확인 완료 처리 성공 (CI/DI 저장 완료, is_identity_verified=True)")

        # 4. 사업자 정보 입력 및 DEV 권한 승인
        print("\n--- [Step 4] 가상 사업자 정보 입력 및 DEV 승인 ---")
        res = client.post("/users/me/business", headers=owner_headers, json={
            "business_number": "123-45-67890",
            "business_name": "요청가게",
            "representative_name": "요청점주",
            "representative_phone": "010-1234-5678",
            "store_name": "요청가맹점",
            "document_url": "/static/images/req_doc.png"
        })
        assert res.status_code == 200, f"사업자 정보 등록 실패: {res.text}"
        print("[OK] 가상 사업자 서류 등록 요청 완료")

        # DEV 권한 계정으로 사업자 정보 승인
        res = client.patch(f"/users/{owner_id}/verify-business", headers=dev_headers, params={"is_verified": True})
        assert res.status_code == 200, f"DEV 사업자 승인 실패: {res.text}"
        print("[OK] DEV 계정에 의한 사업자 상태 승인 완료 (is_business_verified=True)")

        # 5. 테스트 키오스크 생성 및 MANAGER 로 권한 부여
        print("\n--- [Step 5] 키오스크 생성 및 MANAGER 권한 부여 ---")
        # DEV가 키오스크를 직접 매장에 생성
        res = client.post("/kiosks/", headers=dev_headers, json={
            "name": "요청결제시험기",
            "model_name": "K-REQ-TEST",
            "type": "Restaurant",
            "status": "OPERATING", # 즉시 가동상태
            "user_id": owner_id # 점주의 Store에 귀속
        })
        assert res.status_code == 201, f"키오스크 생성 실패: {res.text}"
        kiosk_id = res.json()["id"]
        kiosk_code = res.json()["code"]
        print(f"[OK] 테스트 키오스크 생성 완료 (ID: {kiosk_id}, 코드: {kiosk_code})")

        # 키오스크 생성 시 소유주는 MASTER로 자동 매핑됨.
        # 따라서, 점주(owner_id)의 자동 등록된 권한을 MASTER에서 MANAGER로 수정하여 부여함
        res = client.patch(f"/kiosks/{kiosk_id}/admins/{owner_id}", headers=dev_headers, json={
            "role": "MANAGER"
        })
        assert res.status_code == 200, f"MANAGER 권한 수정 실패: {res.text}"
        print("[OK] 자동으로 등록된 점주(owner)의 권한을 MANAGER로 성공적 변경 완료")

        # 6. 테스트 상품 등록 (3종 등록, 이미지는 바탕화면 경로)
        print("\n--- [Step 6] 테스트 상품 등록 (3종) ---")
        # 6-1. 매대 생성
        res = client.post(f"/shelves/kiosk/{kiosk_id}/shelve", headers=dev_headers, json={
            "name": "요청결제시험매대",
            "terminal_id": "REQ_T1",
            "business_number": "123-45-67890",
            "vender_code": "V_REQ"
        })
        assert res.status_code == 201, f"매대 생성 실패: {res.text}"
        shelve_id = res.json()["id"]
        
        # 6-2. 카테고리 생성
        res = client.post("/categories/", headers=dev_headers, json={
            "name": "음료/음료수",
            "shelve_id": shelve_id
        })
        assert res.status_code == 201, f"카테고리 생성 실패: {res.text}"
        category_id = res.json()["id"]

        # 6-3. 상품 등록 (Pocari 3종)
        image_path = "C:\\Users\\user\\Desktop\\pocari.jpeg"
        products_payload = [
            {"name": "포카리스웨트 250ml", "price": 1500, "stock": 50},
            {"name": "포카리스웨트 500ml", "price": 2200, "stock": 30},
            {"name": "포카리스웨트 1.5L", "price": 3800, "stock": 20}
        ]
        product_ids = []
        for prod in products_payload:
            res = client.post("/products/", headers=dev_headers, json={
                "category_id": category_id,
                "name": prod["name"],
                "price": prod["price"],
                "image": image_path,
                "stock": prod["stock"],
                "stock_managed": True,
                "kiosk_id": kiosk_id
            })
            assert res.status_code == 201, f"상품 등록 실패: {res.text}"
            p_id = res.json()["id"]
            product_ids.append(p_id)
            print(f"  - 상품 등록 완료: {prod['name']} (ID: {p_id})")

        # 7. 다양한 결제 시나리오 실행 (10건)
        print("\n--- [Step 7] 다양한 결제 시나리오 다건 호출 (10건) ---")
        
        scenarios = [
            {"desc": "시나리오 1: 포카리 250ml 1개 단독 구매", "items": [{ "idx": 0, "qty": 1 }]},
            {"desc": "시나리오 2: 포카리 500ml 2개 벌크 구매", "items": [{ "idx": 1, "qty": 2 }]},
            {"desc": "시나리오 3: 포카리 1.5L 1개 + 250ml 2개 혼합 구매", "items": [{ "idx": 2, "qty": 1 }, { "idx": 0, "qty": 2 }]},
            {"desc": "시나리오 4: 전 품목 각 1개씩 세트 구매", "items": [{ "idx": 0, "qty": 1 }, { "idx": 1, "qty": 1 }, { "idx": 2, "qty": 1 }]},
            {"desc": "시나리오 5: 포카리 500ml 3개 단독 구매", "items": [{ "idx": 1, "qty": 3 }]},
            {"desc": "시나리오 6: 포카리 1.5L 2개 단독 대용량 구매", "items": [{ "idx": 2, "qty": 2 }]},
            {"desc": "시나리오 7: 포카리 250ml 4개 단독 대량 구매", "items": [{ "idx": 0, "qty": 4 }]},
            {"desc": "시나리오 8: 포카리 500ml 1개 + 1.5L 1개 소형 세트", "items": [{ "idx": 1, "qty": 1 }, { "idx": 2, "qty": 1 }]},
            {"desc": "시나리오 9: 포카리 250ml 2개 + 500ml 1개 구매", "items": [{ "idx": 0, "qty": 2 }, { "idx": 1, "qty": 1 }]},
            {"desc": "시나리오 10: 포카리 1.5L 3개 대량 구매", "items": [{ "idx": 2, "qty": 3 }]}
        ]

        for i, sc in enumerate(scenarios, 1):
            items_payload = []
            total_amount = 0
            for it in sc["items"]:
                p_id = product_ids[it["idx"]]
                price = products_payload[it["idx"]]["price"]
                qty = it["qty"]
                items_payload.append({"product_id": p_id, "quantity": qty})
                total_amount += (price * qty)
            
            # 가상 승인 결제 요청 호출
            res = client.post("/kiosk_client/pay/mock", json={
                "kiosk_id": kiosk_id,
                "total_amount": total_amount,
                "payment_method": "카드",
                "order_no": f"010-0000-{1000 + i}",
                "items": items_payload
            })
            assert res.status_code == 200, f"결제 시나리오 {i} 실패: {res.text}"
            res_data = res.json()
            print(f"[OK] {sc['desc']} -> 성공! (주문번호: {res_data['order_no']}, 승인번호: {res_data['approval_code']}, 금액: {total_amount}원)")

        print("\n==============================================")
        print("[SUCCESS] 모든 요청 검증 시나리오 성공 통과!")
        print("==============================================")

    except Exception as e:
        print(f"\n[FAIL] 요청 시나리오 검증 에러: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        # 데이터 정리 수행 (유저 직접 확인을 위해 DB 삭제 주석 처리)
        # clean_database(owner_email, dev_email)
        print("[TEST KEEP DATA] 유저 확인을 위해 테스트 데이터를 DB에 유지하였습니다.")

if __name__ == "__main__":
    run_requested_test()
