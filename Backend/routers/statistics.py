from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from sqlalchemy import func, select, desc
from datetime import date
from models.order import Order
from models.user import UserInfo, UserRole
from models.order_item import OrderItem
from models.kiosk import Kiosk
from database import get_db
from core.dependency import get_current_user
from typing import Optional
import uuid

router = APIRouter()

@router.get("/summary", summary = "오늘의 대시보드 요약")
def get_dashboard_summary (
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    today_start = date.today()
    month_start = today_start.replace(day=1)

    sales_stmt = select(func.sum(Order.total_amount)).where(Order.created_date >= today_start)
    monthly_stmt = select(func.sum(Order.total_amount)).where(Order.created_date >= month_start)
    order_stmt = select(func.count(Order.id)).where(Order.created_date >= today_start)

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        sales_stmt = sales_stmt.where(Order.kiosk_id == x_kiosk_id)
        monthly_stmt = monthly_stmt.where(Order.kiosk_id == x_kiosk_id)
        order_stmt = order_stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return {
                "today_sales" : 0,
                "today_orders" : 0,
                "monthly_sales": 0
            }
        sales_stmt = sales_stmt.where(Order.kiosk_id.in_(kiosk_ids))
        monthly_stmt = monthly_stmt.where(Order.kiosk_id.in_(kiosk_ids))
        order_stmt = order_stmt.where(Order.kiosk_id.in_(kiosk_ids))

    total_sales = db.scalar(sales_stmt) or 0
    monthly_sales = db.scalar(monthly_stmt) or 0
    total_order = db.scalar(order_stmt) or 0

    return {
        "today_sales" : total_sales,
        "today_orders" : total_order,
        "monthly_sales": monthly_sales
    }


@router.get("/best-sellers", summary="오늘의 베스트셀러 Top 5")
def get_best_sellers(
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    today_start = date.today()

    stmt = (
        select(OrderItem.product_name, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.created_date >= today_start)
    )

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = (
        stmt.group_by(OrderItem.product_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    )

    result = db.execute(stmt).all()

    best_seller_list = []
    for row in result:
        best_seller_list.append({"product_name": row[0], "total_sold": row[1]})

    return best_seller_list


@router.get("/settlement", summary="월간 정산 현황 (일별 매출 및 환불액 집계)")
def get_monthly_settlement(
    year: int,
    month: int,
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    """
    지정된 연도와 월에 속하는 가동 키오스크의 일별 매출 합계, 주문 수 및 환불 집계 내역을 반환합니다.
    """
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="대시보드 권한이 없습니다."
        )

    try:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 연도 또는 월입니다.")

    stmt = (
        select(
            func.date(Order.created_date).label("date"),
            func.sum(Order.total_amount).label("sales"),
            func.count(Order.id).label("orders"),
            func.sum(func.coalesce(Order.refund_amount, 0)).label("refunds")
        )
        .where(
            Order.created_date >= start_date,
            Order.created_date < end_date,
            Order.status.in_(["Completed", "REFUNDED"])
        )
    )

    # X-Kiosk-Id 헤더 필터 추가
    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    # MANAGER 권한인 경우 본인 키오스크의 데이터만 필터링
    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = stmt.group_by(func.date(Order.created_date)).order_by(func.date(Order.created_date).asc())
    results = db.execute(stmt).all()

    settlement_list = []
    for row in results:
        settlement_list.append({
            "date": str(row[0]),
            "sales": int(row[1] or 0),
            "orders": int(row[2] or 0),
            "refunds": int(row[3] or 0)
        })

    return settlement_list


# -----------------------------------------------------------------------------
# [초보자 가이드 - 세부 통계 API]
# 파트너센터의 시각적인 차트 렌더링에 적합한 데이터 구조로
# 최근 매출 트렌드, 결제수단 비중, 시간대별 성과를 집계하여 반환합니다.
# -----------------------------------------------------------------------------

@router.get("/stats/sales-trend", summary="최근 7일간의 매출 추이 (꺾은선 차트용)")
def get_sales_trend(
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="대시보드 권한이 없습니다.")

    # 최근 7일간의 매출 데이터를 일별로 조회합니다.
    from datetime import timedelta
    today = date.today()
    start_date = today - timedelta(days=6) # 오늘 포함 7일

    stmt = (
        select(
            func.date(Order.created_date).label("date"),
            func.sum(Order.total_amount).label("sales"),
            func.sum(func.coalesce(Order.refund_amount, 0)).label("refunds")
        )
        .where(
            Order.created_date >= start_date,
            Order.status.in_(["Completed", "REFUNDED"])
        )
    )

    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = stmt.group_by(func.date(Order.created_date)).order_by(func.date(Order.created_date).asc())
    results = db.execute(stmt).all()

    # 빈 날짜도 차트에 0으로 부드럽게 채워주기 위해 딕셔너리로 우선 매핑합니다.
    trend_dict = {str(row[0]): {"sales": int(row[1] or 0), "refunds": int(row[2] or 0)} for row in results}
    
    trend_list = []
    for i in range(7):
        day = start_date + timedelta(days=i)
        day_str = str(day)
        day_data = trend_dict.get(day_str, {"sales": 0, "refunds": 0})
        trend_list.append({
            "date": day.strftime("%m/%d"),
            "sales": day_data["sales"],
            "refunds": day_data["refunds"],
            "net_sales": day_data["sales"] - day_data["refunds"]
        })

    return trend_list


@router.get("/stats/payment-methods", summary="오늘의 결제 수단별 점유율 (도넛 차트용)")
def get_payment_methods(
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="대시보드 권한이 없습니다.")

    today_start = date.today()

    stmt = (
        select(
            Order.payment_method,
            func.count(Order.id).label("count"),
            func.sum(Order.total_amount).label("amount")
        )
        .where(
            Order.created_date >= today_start,
            Order.status == "Completed"
        )
    )

    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = stmt.group_by(Order.payment_method)
    results = db.execute(stmt).all()

    method_list = []
    for row in results:
        method_name = row[0]
        # 한글 가독성을 위해 한글명 매핑
        ko_name = "신용카드"
        if method_name.upper() == "CASH": ko_name = "현금"
        elif method_name.upper() == "KAKAOPAY": ko_name = "카카오페이"
        elif method_name.upper() == "NAVERPAY": ko_name = "네이버페이"
        elif method_name.upper() == "TOSSPAY": ko_name = "토스페이"
        elif method_name.upper() == "VIRTUAL_ACCOUNT": ko_name = "가상계좌"

        method_list.append({
            "method": method_name,
            "name": ko_name,
            "count": int(row[1] or 0),
            "amount": int(row[2] or 0)
        })

    return method_list


@router.get("/stats/hourly", summary="오늘의 시간대별 매출 추이 (막대 차트용)")
def get_hourly_stats(
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="대시보드 권한이 없습니다.")

    today_start = date.today()

    # PostgreSQL의 EXTRACT HOUR를 사용해 시간대별 집계를 수행합니다.
    from sqlalchemy import extract
    stmt = (
        select(
            extract('hour', Order.created_date).label("hour"),
            func.sum(Order.total_amount).label("sales"),
            func.count(Order.id).label("orders")
        )
        .where(
            Order.created_date >= today_start,
            Order.status == "Completed"
        )
    )

    if x_kiosk_id:
        stmt = stmt.where(Order.kiosk_id == x_kiosk_id)

    if current_user.role == UserRole.MANAGER:
        kiosk_ids = db.scalars(select(Kiosk.id).where(Kiosk.user_id == current_user.id)).all()
        if not kiosk_ids:
            return []
        stmt = stmt.where(Order.kiosk_id.in_(kiosk_ids))

    stmt = stmt.group_by(extract('hour', Order.created_date)).order_by(extract('hour', Order.created_date).asc())
    results = db.execute(stmt).all()

    # 시간대별 맵핑 (0시 ~ 23시)
    hourly_dict = {int(row[0]): {"sales": int(row[1] or 0), "orders": int(row[2] or 0)} for row in results}
    
    hourly_list = []
    # 영업시간 위주로 보기 위해 09시부터 22시까지 데이터를 기본 반환하도록 루프를 돕니다.
    for h in range(9, 23):
        h_data = hourly_dict.get(h, {"sales": 0, "orders": 0})
        hourly_list.append({
            "hour": f"{h}시",
            "sales": h_data["sales"],
            "orders": h_data["orders"]
        })

    return hourly_list


# -----------------------------------------------------------------------------
# [초보자 가이드 - CSV 스트리밍 응답 (StreamingResponse)]
# 대용량 정산 데이터를 한 번에 메모리에 올리지 않고,
# 줄 단위로 클라이언트에 스트리밍 전송하여 메모리 효율성을 극대화합니다.
# 또한, Excel에서 한글이 깨지지 않도록 UTF-8 BOM 마커(\ufeff)를 파일 맨 앞에 붙여 전송합니다.
# -----------------------------------------------------------------------------
from fastapi.responses import StreamingResponse
import io
import csv

@router.get("/settlement/download", summary="월간 정산 데이터 CSV 다운로드")
def download_settlement_csv(
    year: int,
    month: int,
    x_kiosk_id: Optional[uuid.UUID] = Header(None, alias="X-Kiosk-Id"),
    db: Session = Depends(get_db),
    current_user: UserInfo = Depends(get_current_user)
):
    if current_user.role not in [UserRole.DEV, UserRole.HEAD, UserRole.MASTER, UserRole.MANAGER]:
        raise HTTPException(status_code=403, detail="다운로드 권한이 없습니다.")

    # 1. 월간 정산 데이터 목록 조회
    settlement_data = get_monthly_settlement(year=year, month=month, x_kiosk_id=x_kiosk_id, db=db, current_user=current_user)

    # 2. 인메모리 문자열 버퍼 생성 및 CSV 라이터 설정
    output = io.StringIO()
    # 엑셀과의 한글 인코딩 호환성을 보장하기 위해 UTF-8 BOM 헤더를 수동 추가합니다.
    output.write('\ufeff')
    
    writer = csv.writer(output)
    
    # 3. CSV 헤더 및 데이터 행 작성
    writer.writerow(["일자", "총 매출액 (원)", "결제 건수 (건)", "총 환불액 (원)", "순 매출액 (원)"])
    
    for row in settlement_data:
        net_sales = row["sales"] - row["refunds"]
        writer.writerow([
            row["date"],
            row["sales"],
            row["orders"],
            row["refunds"],
            net_sales
        ])
        
    # 버퍼 커서를 맨 앞으로 돌려 읽을 준비를 합니다.
    output.seek(0)
    
    # 4. 다운로드 파일명 구성
    filename = f"moki_settlement_{year}_{str(month).padStart(2, '0')}.csv"
    if x_kiosk_id:
        filename = f"moki_settlement_{x_kiosk_id.hex[:8]}_{year}_{str(month).padStart(2, '0')}.csv"

    # 스트리밍 응답으로 클라이언트에게 CSV 바이너리를 전송합니다.
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv; charset=utf-8-sig",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

