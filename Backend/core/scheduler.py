# Backend/core/scheduler.py
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from database import DB_session
from models.kiosk import Kiosk
from models.billing_product import BillingProduct, KioskBillingHistory
import httpx
import uuid
from core.security import PORTONE_API_SECRET, PORTONE_CHANNEL_KEY, PORTONE_API_URL

# 로깅 설정
logger = logging.getLogger("subscription_scheduler")
logger.setLevel(logging.INFO)

async def check_kiosk_subscriptions():
    """
    [초보자 가이드 - 정기결제 스케줄러 배치]
    매시간 만료일이 지난 키오스크를 스캔하여 등록된 빌링키로 자동 결제를 진행합니다.
    결제 성공 시 이용 기간을 연장하고, 결제 실패 시 24시간의 유예 경고(WARNING) 상태를 부여하여
    유예 기간 초과 시 최종 사용 정지(WAITING)로 전환합니다.
    """
    while True:
        try:
            logger.info("정기결제 만료 키오스크 탐색 시작...")
            db = DB_session()
            try:
                # 다음 결제일이 현재 시간보다 이전이고, 빌링키가 등록된 모든 키오스크 조회
                stmt = select(Kiosk).where(
                    Kiosk.billing_key.isnot(None),
                    Kiosk.next_payment_date <= datetime.now()
                )
                expired_kiosks = db.execute(stmt).scalars().all()
                
                for kiosk in expired_kiosks:
                    logger.info(f"키오스크 정기결제 처리 대상 감지: {kiosk.name} (코드: {kiosk.code}, 상태: {kiosk.status})")
                    
                    # 1. 마지막으로 사용한 요금 상품의 결제 금액 추적
                    amount = 33000
                    period_months = 1
                    product_id = None
                    order_name = "MOKI 키오스크 월 이용료 (자동)"

                    history_stmt = (
                        select(KioskBillingHistory)
                        .where(KioskBillingHistory.kiosk_id == kiosk.id)
                        .order_by(KioskBillingHistory.id.desc())
                        .limit(1)
                    )
                    last_history = db.execute(history_stmt).scalar_one_or_none()
                    
                    if last_history and last_history.product:
                        amount = last_history.product.amount
                        period_months = last_history.product.period_months
                        product_id = last_history.billing_product_id
                        order_name = f"MOKI 서비스 이용 요금 - {last_history.product.name} (자동)"

                    # 2. 유예 경고 기간(WARNING) 만료로 인한 최종 정지 처리 분기
                    # 이미 WARNING 상태에서 다음 결제 예정일(유예 만료 시각)이 지난 경우 
                    # 즉시 최종 정지(WAITING) 상태로 전환합니다.
                    if kiosk.status == "WARNING":
                        logger.warning(f"유예 기간이 초과하여 키오스크 서비스 최종 정지 처리합니다: {kiosk.name}")
                        kiosk.status = "WAITING"
                        kiosk.payment_status = "UNPAID"
                        # 정기 결제 이력에 실패 기록 적재
                        failed_history = KioskBillingHistory(
                            kiosk_id=kiosk.id,
                            billing_product_id=product_id,
                            billing_type="REGULAR",
                            amount=amount,
                            status="FAILED",
                            error_message="정기 결제 연체 및 24시간 유예 기간 초과로 최종 서비스 정지",
                            payment_date=datetime.now()
                        )
                        db.add(failed_history)
                        continue

                    # 3. 결제 시도
                    success = False
                    approval_code = f"AUTO_{uuid.uuid4().hex[:8].upper()}"
                    error_msg = None

                    # 포트원 V2 실결제 연동 분기
                    if PORTONE_API_SECRET and PORTONE_API_SECRET != "test_portone_secret":
                        payment_id = f"pay_sub_auto_{uuid.uuid4().hex[:14]}"
                        url = f"{PORTONE_API_URL}/payments/{payment_id}/billing-key"
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"PortOne {PORTONE_API_SECRET}"
                        }
                        payload = {
                            "billingKey": kiosk.billing_key,
                            "orderName": order_name,
                            "amount": {
                                "total": amount
                            },
                            "currency": "KRW",
                            "channelKey": PORTONE_CHANNEL_KEY
                        }
                        
                        try:
                            async with httpx.AsyncClient() as client:
                                res = await client.post(url, headers=headers, json=payload, timeout=10.0)
                                
                            if res.status_code == 200:
                                res_data = res.json()
                                approval_code = res_data.get("payment", {}).get("pgTxId") or approval_code
                                success = True
                            else:
                                error_msg = res.json().get("message") or res.text
                                logger.warning(f"정기결제 자동 승인 실패 (PortOne): {kiosk.name} - {error_msg}")
                        except Exception as pay_err:
                            error_msg = str(pay_err)
                            logger.error(f"정기결제 자동 승인 통신 에러: {kiosk.name} - {error_msg}")
                    else:
                        # [모킹 자동 승인]
                        if "FAIL" in kiosk.billing_key.upper():
                            error_msg = "한도초과/잔액부족 모킹 실패"
                            logger.warning(f"정기결제 승인 실패 (모킹): {kiosk.name}")
                        else:
                            success = True
                            logger.info(f"정기결제 승인 완료 (모킹): {kiosk.name} - {amount}원 결제")

                    # 4. 결제 결과 처리
                    if success:
                        # 결제 성공: 정상 개통 처리 및 +30일(이용 개월 수 기준) 연장
                        kiosk.payment_status = "NORMAL"
                        kiosk.status = "OPERATING"
                        kiosk.next_payment_date = datetime.now() + timedelta(days=30 * period_months)
                        
                        # 히스토리 추가
                        success_history = KioskBillingHistory(
                            kiosk_id=kiosk.id,
                            billing_product_id=product_id,
                            billing_type="REGULAR",
                            amount=amount,
                            status="SUCCESS",
                            payment_date=datetime.now()
                        )
                        db.add(success_history)
                    else:
                        # 결제 실패: 즉각 정지하지 않고 24시간 결제 유예(WARNING)로 전환
                        kiosk.payment_status = "UNPAID"
                        kiosk.status = "WARNING"
                        # 유예 만료 예정일을 24시간 뒤로 설정
                        kiosk.next_payment_date = datetime.now() + timedelta(hours=24)
                        
                        # 히스토리 추가
                        failed_history = KioskBillingHistory(
                            kiosk_id=kiosk.id,
                            billing_product_id=product_id,
                            billing_type="REGULAR",
                            amount=amount,
                            status="FAILED",
                            error_message=f"자동 결제 실패: {error_msg} (24시간 유예 경고 상태 부여)",
                            payment_date=datetime.now()
                        )
                        db.add(failed_history)
                        
                        # (비즈니스 로직) 카카오 결제 실패 알림톡 연동 (여기서는 로깅)
                        logger.warning(f"정기결제 실패 알림톡 송출 완료 -> 수신자: 점주, 내용: [{kiosk.name}] 이용료 자동결제 실패. 24시간 내 카드 교체 요망.")

                db.commit()
            except Exception as e:
                db.rollback()
                logger.error(f"스케줄러 작업 중 DB 오류 발생: {str(e)}")
            finally:
                db.close()
                
        except Exception as ex:
            logger.error(f"스케줄러 메인 루프 예외 발생: {str(ex)}")
            
        # 매시간(3600초) 대기 후 반복 실행
        await asyncio.sleep(3600)

def start_scheduler(app):
    """
    FastAPI 서버 구동 시 백그라운드 태스크로 스케줄러를 등록합니다.
    """
    @app.on_event("startup")
    async def startup_event():
        logger.info("키오스크 이용료 정기결제 백그라운드 스케줄러를 가동합니다.")
        asyncio.create_task(check_kiosk_subscriptions())

