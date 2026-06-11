import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from database import DB_session
from models.kiosk import Kiosk
import httpx
import uuid
from core.security import PORTONE_API_SECRET, PORTONE_CHANNEL_KEY, PORTONE_API_URL

# 로깅 설정
logger = logging.getLogger("subscription_scheduler")
logger.setLevel(logging.INFO)

async def check_kiosk_subscriptions():
    """
    정기결제 기기 스케줄러 작업 루프
    매시간 만료된 기기를 탐색해 등록된 빌링키로 자동 결제를 시도합니다.
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
                    logger.info(f"키오스크 정기결제 처리 대상 감지: {kiosk.name} (코드: {kiosk.code})")
                    
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
                            "orderName": "MOKI 키오스크 월 이용료 (자동)",
                            "amount": {
                                "total": 33000
                            },
                            "currency": "KRW",
                            "channelKey": PORTONE_CHANNEL_KEY
                        }
                        
                        try:
                            async with httpx.AsyncClient() as client:
                                res = await client.post(url, headers=headers, json=payload, timeout=10.0)
                                
                            if res.status_code == 200:
                                logger.info(f"정기결제 자동 승인 완료 (PortOne): {kiosk.name} - 33,000원")
                                kiosk.payment_status = "NORMAL"
                                kiosk.status = "OPERATING"
                                kiosk.next_payment_date = datetime.now() + timedelta(days=30)
                            else:
                                error_msg = res.text
                                logger.warning(f"정기결제 자동 승인 실패 (PortOne): {kiosk.name} - {error_msg}")
                                kiosk.payment_status = "UNPAID"
                                kiosk.status = "SUSPENDED"
                        except Exception as pay_err:
                            logger.error(f"정기결제 자동 승인 통신 에러: {kiosk.name} - {str(pay_err)}")
                            kiosk.payment_status = "UNPAID"
                            kiosk.status = "SUSPENDED"
                    else:
                        # [모킹 자동 승인]
                        # 빌링키 이름에 'FAIL'이 포함되어 있으면 모의 실패 처리, 그 외에는 성공 처리합니다.
                        if "FAIL" in kiosk.billing_key.upper():
                            logger.warning(f"정기결제 승인 실패 (한도초과/잔액부족 모킹): {kiosk.name}")
                            kiosk.payment_status = "UNPAID"
                            kiosk.status = "SUSPENDED" # 이용 정지
                        else:
                            logger.info(f"정기결제 승인 완료 (모킹): {kiosk.name} - 33,000원 결제")
                            kiosk.payment_status = "NORMAL"
                            kiosk.status = "OPERATING"
                            kiosk.next_payment_date = datetime.now() + timedelta(days=30)
                
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
